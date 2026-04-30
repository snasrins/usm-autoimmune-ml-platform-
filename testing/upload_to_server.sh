#!/bin/bash
# Upload optimized code to GPU server
# Run this from your Windows PowerShell or WSL

echo "🚀 Uploading optimized standalone_unstructured_pipeline.py to gpulab1..."

# Upload via SCP
scp standalone_unstructured_pipeline.py shaggy@gpulab1:~/usm-autoimmune-ml-platform/

echo "✅ Upload complete!"
echo ""
echo "📝 Next steps:"
echo "   1. SSH into gpulab1:"
echo "      ssh shaggy@gpulab1"
echo ""
echo "   2. Activate virtual environment:"
echo "      source venv_qwen3/bin/activate"
echo ""
echo "   3. Test optimized code:"
echo "      python standalone_unstructured_pipeline.py \"Sample Medical Report.pdf\""
echo ""
echo "   Expected: ~90-120s total (down from 376s)"
