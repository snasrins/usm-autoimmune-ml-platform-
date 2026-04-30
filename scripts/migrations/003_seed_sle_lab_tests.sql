-- ============================================================================
-- Seed Lab Test Definitions - SLE Dataset (61 tests)
-- ============================================================================

-- Hematology - Complete Blood Count (5 tests)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('wbc', 'WBC', 'Hematology', 'numeric', '10^9/L', '{"min": 3.5, "max": 9.5}'::jsonb, ARRAY['SLE'], true),
('neu_percent', 'NEU%', 'Hematology', 'numeric', '%', '{"min": 50, "max": 70}'::jsonb, ARRAY['SLE'], true),
('lym_percent', 'LYM%', 'Hematology', 'numeric', '%', '{"min": 20, "max": 40}'::jsonb, ARRAY['SLE'], true),
('hgb', 'HGB', 'Hematology', 'numeric', 'g/L', '{"min": 115, "max": 150}'::jsonb, ARRAY['SLE'], true),
('plt', 'PLT', 'Hematology', 'numeric', '10^9/L', '{"min": 125, "max": 350}'::jsonb, ARRAY['SLE'], true);

-- Inflammation Markers (4 tests)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('crp', 'CRP', 'Inflammation', 'numeric', 'mg/L', '{"min": 0, "max": 10}'::jsonb, ARRAY['SLE', 'RA', 'Sjogren'], true),
('esr', 'ESR', 'Inflammation', 'numeric', 'mm/h', '{"min": 0, "max": 20}'::jsonb, ARRAY['SLE', 'RA', 'Sjogren'], true),
('alb', 'ALB', 'Inflammation', 'numeric', 'g/L', '{"min": 40, "max": 55}'::jsonb, ARRAY['SLE'], true),
('glo', 'GLO', 'Inflammation', 'numeric', 'g/L', '{"min": 20, "max": 40}'::jsonb, ARRAY['SLE'], true);

-- Kidney Function (4 tests)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('urinary_protein_qual', 'Urinary protein', 'Kidney_Function', 'qualitative', '', '{"normal": "negative"}'::jsonb, ARRAY['SLE'], true),
('urine_protein_quant', 'Urine protein quantification', 'Kidney_Function', 'numeric', 'g/L', '{"max": 0.15}'::jsonb, ARRAY['SLE'], true),
('acr', 'ACR', 'Kidney_Function', 'numeric', 'mg/mmol', '{"max": 3.5}'::jsonb, ARRAY['SLE'], true),
('urine_protein_24h', '24-hour urine protein quantification', 'Kidney_Function', 'numeric', 'g/24h', '{"max": 0.15}'::jsonb, ARRAY['SLE'], true);

-- Immune Cells (5 tests)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('cd3', 'CD3', 'Immune_Cells', 'numeric', '%', '{"min": 60, "max": 75.4}'::jsonb, ARRAY['SLE'], true),
('cd4', 'CD4', 'Immune_Cells', 'numeric', '%', '{"min": 29.4, "max": 45.8}'::jsonb, ARRAY['SLE'], true),
('cd8', 'CD8', 'Immune_Cells', 'numeric', '%', '{"min": 18.2, "max": 32.8}'::jsonb, ARRAY['SLE'], true),
('nk', 'NK', 'Immune_Cells', 'numeric', '%', '{"min": 8, "max": 26}'::jsonb, ARRAY['SLE'], true),
('cd19', 'CD19', 'Immune_Cells', 'numeric', '%', '{"min": 9, "max": 14.1}'::jsonb, ARRAY['SLE'], true);

-- Complement System (2 tests)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('c3', 'C3', 'Complement', 'numeric', 'g/L', '{"min": 0.7, "max": 1.4}'::jsonb, ARRAY['SLE'], true),
('c4', 'C4', 'Complement', 'numeric', 'g/L', '{"min": 0.1, "max": 0.4}'::jsonb, ARRAY['SLE'], true);

-- Immunoglobulins (4 tests)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('igg', 'IgG', 'Immunoglobulin', 'numeric', 'g/L', '{"min": 8.6, "max": 17.4}'::jsonb, ARRAY['SLE', 'Sjogren'], true),
('igm', 'IgM', 'Immunoglobulin', 'numeric', 'g/L', '{"min": 0.46, "max": 3.04}'::jsonb, ARRAY['SLE'], true),
('ige', 'IgE', 'Immunoglobulin', 'numeric', 'IU/ml', '{"min": 0, "max": 165}'::jsonb, ARRAY['SLE'], true),
('iga', 'IgA', 'Immunoglobulin', 'numeric', 'g/L', '{"min": 1.0, "max": 4.2}'::jsonb, ARRAY['SLE'], true);

-- Disease Activity Score (1 test)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, description, is_active) VALUES
('sledai', 'SLEDAI', 'Clinical_Score', 'numeric', 'score', '{"mild": {"min": 0, "max": 6}, "moderate": {"min": 7, "max": 12}, "severe": {"min": 13}}'::jsonb, ARRAY['SLE'], 'SLE Disease Activity Index', true);

-- Autoantibodies - Primary Panel (19 tests)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('ana', 'ANA', 'Autoantibody', 'qualitative', 'titer', '{"negative": "<1:40"}'::jsonb, ARRAY['SLE', 'Sjogren', 'SSc'], true),
('nrnp_sm', 'nRNP/Sm', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE', 'MCTD'], true),
('sm', 'SM', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE'], true),
('ssa', 'SSA', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE', 'Sjogren'], true),
('ro_52', 'RO-52', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE', 'Sjogren'], true),
('ssb', 'SSB', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE', 'Sjogren'], true),
('scl70', 'Scl70', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SSc'], true),
('jo1', 'Jo1', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['Myositis'], true),
('cenpb', 'CENPB', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SSc'], true),
('ds_dna', 'dsDNA', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE'], true),
('nucleosome', 'Nucleosome', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE'], true),
('histone', 'Histone', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE'], true),
('ribosomal_p', 'Ribosomal P protein', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE'], true),
('rnp70', 'RNP70', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SLE', 'MCTD'], true),
('jo_1_dup', 'JO-1', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['Myositis'], true),
('scl_70_dup', 'Scl-70', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['SSc'], true),
('ama_2', 'AMA-2', 'Autoantibody', 'qualitative', '', '{"negative": "negative"}'::jsonb, ARRAY['PBC'], true);

-- Antiphospholipid Antibodies (3 tests)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('anti_beta2_gp', 'Anti-β 2 glycoprotein Ig(GAM)', 'Antiphospholipid', 'numeric', 'AU/ml', '{"min": 0, "max": 20}'::jsonb, ARRAY['SLE', 'APS'], true),
('anticardiolipin_igg', 'Anticardiolipin antibody IgG', 'Antiphospholipid', 'numeric', 'GPLU/ml', '{"min": 0, "max": 10}'::jsonb, ARRAY['SLE', 'APS'], true),
('anticardiolipin_igm', 'Anticardiolipin anti-antibody IGM', 'Antiphospholipid', 'numeric', 'MPLU/ml', '{"min": 0, "max": 10}'::jsonb, ARRAY['SLE', 'APS'], true);

-- ANCA Panel (3 tests)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('pr3', 'PR3', 'ANCA', 'numeric', 'AU/ml', '{"min": 0, "max": 15}'::jsonb, ARRAY['GPA', 'Vasculitis'], true),
('gbm', 'GBM', 'ANCA', 'numeric', 'AU/ml', '{"min": 0, "max": 10}'::jsonb, ARRAY['GPA', 'Goodpasture'], true),
('mpo', 'MPO', 'ANCA', 'numeric', 'AU/ml', '{"min": 0, "max": 15}'::jsonb, ARRAY['MPA', 'Vasculitis'], true);

-- Vitamins (1 test)
INSERT INTO lab_test_definitions (test_code, test_name, test_category, data_type, unit, default_reference_range, relevant_diseases, is_active) VALUES
('vitamin_d_25oh', '25-OH VitD', 'Vitamin', 'numeric', 'ng/ml', '{"min": 20, "max": 80}'::jsonb, ARRAY['SLE', 'RA', 'Sjogren'], true);

-- Summary
SELECT COUNT(*) as total_sle_tests_seeded FROM lab_test_definitions WHERE 'SLE' = ANY(relevant_diseases);
SELECT test_category, COUNT(*) as count FROM lab_test_definitions GROUP BY test_category ORDER BY count DESC;
