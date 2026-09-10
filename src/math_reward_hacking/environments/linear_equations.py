import random

class LinearEquationGenerator:
    def __init__(self, seed: int = 42, min_val: int = -50, max_val: int = 50):
        self.rng = random.Random(seed)
        self.min_val = min_val
        self.max_val = max_val

    def generate(self, problem_id: int):
        """
        Generates a linear equation ax + b = c where x is a unique integer.
        Samples x, a (nonzero), and b, then computes c = ax + b.
        Returns a dictionary containing the prompt, the correct answer, and metadata.
        """
        # Sample x
        x = self.rng.randint(self.min_val, self.max_val)
        
        # Sample a (must not be zero)
        a = self.rng.randint(self.min_val, self.max_val)
        while a == 0:
            a = self.rng.randint(self.min_val, self.max_val)
            
        # Sample b
        b = self.rng.randint(self.min_val, self.max_val)
        
        # Compute c
        c = a * x + b
        
        # Format the equation string nicely
        b_str = f"+ {b}" if b >= 0 else f"- {abs(b)}"
        equation = f"{a}x {b_str} = {c}"
        
        prompt = (
            f"Solve for x: {equation}. "
            "Please reason step-by-step, and provide your final answer."
        )
        
        return {
            "problem_id": problem_id,
            "prompt": prompt,
            "answer": str(x),
            "equation": equation,
            "a": a,
            "b": b,
            "c": c,
            "x": x
        }

    def generate_dataset(self, num_samples: int):
        return [self.generate(i) for i in range(num_samples)]
