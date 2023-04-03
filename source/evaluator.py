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
    
class SortProblem(Problem):
    def evaluate_share(self, evl_ans : str) -> int:
        '''
        Evaluate answer share of correct pairs of answers
        '''
        # if len(evl_ans) > len(self.ref_ans):
        #     raise ValueError('evaluated answer is longer that reference answer') 
        

        def get_pairs_from_array(array : np.ndarray) -> set:
            pairs = set()
            for i in range(len(array)):
                for j in range(i+1, len(array)):
                    # if pairs already contains inverse pair drop both 
                    if (array[j], array[i]) in pairs:
                        pairs.remove((array[j], array[i]))
                    else:
                        pairs.add((array[i], array[j]))
            return pairs
        
        evl_pairs = get_pairs_from_array(evl_ans)
        ref_pairs = get_pairs_from_array(self.ref_ans)

        correct_share = len(evl_pairs & ref_pairs) / len(ref_pairs)
        
        return correct_share
        