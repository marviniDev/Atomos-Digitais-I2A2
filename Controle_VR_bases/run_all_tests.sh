#!/bin/bash
# Script para executar todos os testes do sistema VR/VA

echo "🚀 Executando todos os testes do sistema VR/VA..."
echo "=================================================="

# Lista de testes em ordem de execução
tests=(
    "test_db_initialization.py"
    "test_real_data.py"
    "test_vr_agent_simulation.py"
    "test_table_missing.py"
    "test_fixed_clear_all.py"
    "test_real_data_fixed.py"
)

# Contadores
total_tests=${#tests[@]}
passed_tests=0
failed_tests=0

# Executar cada teste
for test in "${tests[@]}"; do
    echo ""
    echo "🧪 Executando $test..."
    echo "----------------------------------------"
    
    if python3 "$test"; then
        echo "✅ $test - PASSOU"
        ((passed_tests++))
    else
        echo "❌ $test - FALHOU"
        ((failed_tests++))
    fi
done

# Resumo final
echo ""
echo "=================================================="
echo "📊 RESUMO DOS TESTES"
echo "=================================================="
echo "Total de testes: $total_tests"
echo "Testes que passaram: $passed_tests"
echo "Testes que falharam: $failed_tests"

if [ $failed_tests -eq 0 ]; then
    echo "🎉 TODOS OS TESTES PASSARAM!"
    exit 0
else
    echo "💥 ALGUNS TESTES FALHARAM!"
    exit 1
fi
