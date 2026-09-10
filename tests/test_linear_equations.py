import pytest
from math_reward_hacking.environments.linear_equations import LinearEquationGenerator

def test_linear_equation_generation():
    generator = LinearEquationGenerator(seed=42)
    sample = generator.generate(problem_id=1)
    
    a, b, c, x = sample["a"], sample["b"], sample["c"], sample["x"]
    assert a != 0
    assert a * x + b == c
    assert sample["answer"] == str(x)
    assert sample["problem_id"] == 1

def test_deterministic_generation():
    gen1 = LinearEquationGenerator(seed=123)
    gen2 = LinearEquationGenerator(seed=123)
    
    assert gen1.generate(1) == gen2.generate(1)
    assert gen1.generate(2) == gen2.generate(2)
