import numpy as np

class Problem:
    def __init__(self, ref_ans:str, max_pts: int, min_share: float = 0.5) -> None:
        self.ref_ans = ref_ans
        self.min_share = min_share
        self.max_pts = max_pts


    def evaluate(self, evl_ans: str) -> int:
        share = self.evaluate_share(evl_ans)
        pts = (share - self.min_share) / (1 - self.min_share) * self.max_pts
        return int(max(pts, 0))
        

    def evaluate_share(self, evl_ans : str) -> float:
        raise NotImplementedError('can\'t evaluate share for this problem type')
    

