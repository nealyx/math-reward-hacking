import random

class ModuloArithmeticGenerator:
    def __init__(self, seed: int = 42, tier: int = 1):
        self.rng = random.Random(seed)
        self.tier = tier
        
        # Tier definitions: (a_digits, b_digits, c_digits)
        self.tier_configs = {
            1: (2, 2, 2),  # 2-digit * 2-digit + 2-digit
            2: (3, 2, 3),  # 3-digit * 2-digit + 3-digit
            3: (3, 3, 3),  # 3-digit * 3-digit + 3-digit
            4: (4, 3, 4),  # 4-digit * 3-digit + 4-digit
        }
        
        if self.tier not in self.tier_configs:
            raise ValueError(f"Invalid tier {self.tier}. Must be 1, 2, 3, or 4.")
            
        self.a_digits, self.b_digits, self.c_digits = self.tier_configs[self.tier]

    def _sample_digits(self, num_digits: int) -> int:
        min_val = 10**(num_digits - 1)
        max_val = (10**num_digits) - 1
        return self.rng.randint(min_val, max_val)

    def generate(self, problem_id: int):
        """
        Generates an arithmetic expression a * b + c.
        Returns a dictionary containing the prompt, the correct answer, and metadata.
        """
        a = self._sample_digits(self.a_digits)
        b = self._sample_digits(self.b_digits)
        c = self._sample_digits(self.c_digits)
        
        result = a * b + c
        
        prompt = (
            f"Calculate the exact value of {a} * {b} + {c}. "
            "Please reason step-by-step, and provide your final answer."
        )
        
        return {
            "problem_id": problem_id,
            "prompt": prompt,
            "answer": str(result),
            "equation": f"{a} * {b} + {c}",
            "a": a,
            "b": b,
            "c": c,
            "result": result,
            "ground_truth_mod_10": result % 10,
            "tier": self.tier
        }

    def generate_dataset(self, num_samples: int):
        return [self.generate(i) for i in range(num_samples)]
