"""
Qwen-based OCR & Document Understanding Service
Adapted from ultimate_pipeline2.py for USM Autoimmune Platform
Uses: Qwen3-1.7B (embeddings) + Qwen3-VL-2B-Instruct (vision)
"""
import os
import json
import torch
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from PIL import Image
from io import BytesIO

# Transformers
from transformers import (
    AutoTokenizer, 
    AutoModel,
    Qwen2VLForConditionalGeneration,
    AutoProcessor
)

# PDF Processing
try:
    import fitz  # PyMuPDF
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


# ═══════════════════════════════════════════════════════════
#  DATA STRUCTURES 
# ═══════════════════════════════════════════════════════════

@dataclass
class OCRResult:
    """OCR extraction result"""
    text: str
    confidence: float
    method: str  # 'native_pdf', 'qwen_vision', 'tesseract'
    page: int
    metadata: Dict[str, Any]


@dataclass
class DocumentAnalysis:
    """Complete document analysis"""
    document_id: str
    total_pages: int
    extracted_text: str
    ocr_results: List[OCRResult]
    embeddings: Optional[np.ndarray]
    medical_entities: Optional[List[Dict]]
    tables_detected: int
    figures_detected: int


# ═══════════════════════════════════════════════════════════
#  QWEN3-1.7B EMBEDDING ENGINE 
# ═══════════════════════════════════════════════════════════

class Qwen3EmbeddingEngine:
    """Lightweight text embedding using Qwen3-1.7B"""
    
    def __init__(self, model_name: str = "Qwen/Qwen2-1.5B", device: str = "auto"):
        print("🔧 Loading Qwen3-1.7B for embeddings...")
        
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)
        
        self.model.eval()
        print(f"✅ Embedding model loaded on {self.device}")
    
    def encode(self, texts: List[str], batch_size: int = 8) -> np.ndarray:
        """Generate embeddings with batching"""
        if not texts:
            return np.array([])
            
        embeddings = []
        
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                inputs = self.tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                ).to(self.device)
                
                outputs = self.model(**inputs)
                # Mean pooling
                batch_embeddings = outputs.last_hidden_state.mean(dim=1)
                embeddings.append(batch_embeddings.cpu().numpy())
        
        return np.vstack(embeddings) if embeddings else np.array([])
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode single text"""
        return self.encode([text])[0]


# ═══════════════════════════════════════════════════════════
#  QWEN-VL VISION ENGINE 
# ═══════════════════════════════════════════════════════════

class QwenVisionEngine:
    """Qwen3-VL-2B for image/PDF OCR and understanding"""
    
    def __init__(self, model_name: str = "Qwen/Qwen2-VL-2B-Instruct"):
        print("🖼️ Loading Qwen-VL-2B for vision processing...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
            trust_remote_code=True
        )
        
        self.processor = AutoProcessor.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        print(f"✅ Vision model loaded on {self.device}")
    
    def extract_text_from_image(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """Extract text and medical entities from image"""
        image = Image.open(image_path).convert("RGB")
        
        # Structured prompt for medical documents
        system_prompt = (
            "Extract ALL text from this medical document. "
            "Return JSON: {\"extracted_text\": \"...\", \"medical_entities\": [], "
            "\"document_type\": \"lab_report|prescription|clinical_note\"}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": f"Context: {context}\n\nExtract all text and identify medical entities."}
            ]}
        ]
        
        try:
            inputs = self.processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt"
            ).to(self.model.device)
            
            output = self.model.generate(
                **inputs, 
                max_new_tokens=1024,
                temperature=0.1  # Low temperature for accuracy
            )
            
            decoded = self.processor.decode(output[0], skip_special_tokens=True)
            
            # Parse JSON response
            json_start = decoded.find("{")
            json_end = decoded.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(decoded[json_start:json_end])
            else:
                result = {
                    "extracted_text": decoded,
                    "medical_entities": [],
                    "document_type": "unknown"
                }
                
            return result
            
        except Exception as e:
            print(f"⚠️ Vision extraction failed: {e}")
            return {
                "extracted_text": "",
                "medical_entities": [],
                "document_type": "error",
                "error": str(e)
            }


# ═══════════════════════════════════════════════════════════
#  MAIN OCR SERVICE 
# ═══════════════════════════════════════════════════════════

class QwenOCRService:
    """
    Main service for document processing with Qwen models
    Integrates with existing FileParser
    """
    
    def __init__(self, use_vision: bool = True, use_embeddings: bool = True):
        self.embedding_engine = None
        self.vision_engine = None
        
        if use_embeddings:
            try:
                self.embedding_engine = Qwen3EmbeddingEngine()
            except Exception as e:
                print(f"⚠️ Failed to load embedding engine: {e}")
        
        if use_vision:
            try:
                self.vision_engine = QwenVisionEngine()
            except Exception as e:
                print(f"⚠️ Failed to load vision engine: {e}")
    
    def process_pdf(self, pdf_path: str) -> DocumentAnalysis:
        """
        Process PDF with multi-level fallback:
        1. Try native text extraction (pdfplumber)
        2. If sparse/poor quality, use Qwen-VL on page images
        3. Generate embeddings for semantic search
        """
        if not PDF_AVAILABLE:
            raise RuntimeError("PDF processing libraries not available")
        
        document_id = Path(pdf_path).stem
        ocr_results = []
        all_text = []
        total_pages = 0
        
        # Step 1: Try native text extraction
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    
                    # Check if extraction was successful (heuristic: >50 chars)
                    if len(text.strip()) > 50:
                        ocr_results.append(OCRResult(
                            text=text,
                            confidence=0.95,
                            method="native_pdf",
                            page=page_num,
                            metadata={"width": page.width, "height": page.height}
                        ))
                        all_text.append(text)
                    else:
                        # Poor extraction, flag for vision processing
                        ocr_results.append(OCRResult(
                            text="",
                            confidence=0.0,
                            method="native_pdf_failed",
                            page=page_num,
                            metadata={"requires_vision": True}
                        ))
        except Exception as e:
            print(f"⚠️ Native PDF extraction failed: {e}")
        
        # Step 2: Use Qwen-VL for failed pages
        if self.vision_engine and PDF2IMAGE_AVAILABLE:
            failed_pages = [r for r in ocr_results if r.confidence < 0.5]
            
            if failed_pages:
                print(f"🔍 Running Qwen-VL on {len(failed_pages)} pages...")
                
                # Convert PDF to images
                images = convert_from_path(pdf_path, dpi=300)
                
                for result in failed_pages:
                    page_idx = result.page - 1
                    if page_idx < len(images):
                        # Save temp image
                        temp_path = f"/tmp/page_{result.page}.png"
                        images[page_idx].save(temp_path)
                        
                        # Extract with vision model
                        vision_result = self.vision_engine.extract_text_from_image(
                            temp_path,
                            context=f"Medical document page {result.page}"
                        )
                        
                        # Update result
                        result.text = vision_result.get("extracted_text", "")
                        result.confidence = 0.85
                        result.method = "qwen_vision"
                        result.metadata["medical_entities"] = vision_result.get("medical_entities", [])
                        result.metadata["document_type"] = vision_result.get("document_type", "unknown")
                        
                        all_text.append(result.text)
                        
                        # Cleanup
                        os.remove(temp_path)
        
        # Step 3: Generate embeddings
        combined_text = "\n\n".join(all_text)
        embeddings = None
        
        if self.embedding_engine and combined_text:
            embeddings = self.embedding_engine.encode_single(combined_text)
        
        # Extract medical entities
        medical_entities = []
        for result in ocr_results:
            if "medical_entities" in result.metadata:
                medical_entities.extend(result.metadata["medical_entities"])
        
        return DocumentAnalysis(
            document_id=document_id,
            total_pages=total_pages,
            extracted_text=combined_text,
            ocr_results=ocr_results,
            embeddings=embeddings,
            medical_entities=medical_entities if medical_entities else None,
            tables_detected=0,  # TODO: Integrate table detection
            figures_detected=0   # TODO: Integrate figure detection
        )
    
    def process_image(self, image_path: str, context: str = "") -> OCRResult:
        """Process single image (lab report, clinical note, etc.)"""
        if not self.vision_engine:
            raise RuntimeError("Vision engine not initialized")
        
        result = self.vision_engine.extract_text_from_image(image_path, context)
        
        return OCRResult(
            text=result.get("extracted_text", ""),
            confidence=0.85,
            method="qwen_vision",
            page=1,
            metadata={
                "medical_entities": result.get("medical_entities", []),
                "document_type": result.get("document_type", "unknown")
            }
        )
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for semantic search"""
        if not self.embedding_engine:
            raise RuntimeError("Embedding engine not initialized")
        
        return self.embedding_engine.encode(texts)


# ═══════════════════════════════════════════════════════════
#  EXAMPLE USAGE 
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Initialize service
    service = QwenOCRService(use_vision=True, use_embeddings=True)
    
    # Example: Process PDF
    # result = service.process_pdf("lab_report.pdf")
    # print(f"Extracted {len(result.extracted_text)} characters")
    # print(f"Medical entities: {result.medical_entities}")
    
    print("✅ Qwen OCR Service ready!")
