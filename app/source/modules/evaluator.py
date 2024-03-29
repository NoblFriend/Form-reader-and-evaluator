import numpy as np
import pandas as pd


class Problem:
    def __init__(self, ref_ans: str, max_pts: int) -> None:
        self.ref_ans = ref_ans
        self.max_pts = max_pts

    def evaluate(self, evl_ans: str) -> int:
        share = self.evaluate_share(evl_ans)
        pts = (share - self.min_share) / (1 - self.min_share) * self.max_pts
        return round(max(pts, 0))

    def evaluate_share(self, evl_ans: str) -> float:
        raise NotImplementedError(
            'can\'t evaluate share for this problem type')


class SortProblem(Problem):
    def __init__(self, ref_ans: str, max_pts: int, min_share: float = 0.5) -> None:
        super().__init__(ref_ans, max_pts)
        self.min_share = min_share

    def evaluate_share(self, evl_ans: str) -> int:
        '''
        Evaluate answer share of correct pairs of answers
        '''
        if len(evl_ans) > len(self.ref_ans):
            raise ValueError(
                'Evaluated answer is longer that reference answer')

        def get_pairs_from_array(array: np.ndarray) -> set:
            pairs = set()
            for i in range(len(array)):
                for j in range(i+1, len(array)):
                    pairs.add((array[i], array[j]))
            for a, b in pairs.copy():
                if a == b:
                    pairs.remove((a, b))
                if (b, a) in pairs:
                    pairs.remove((a, b))
                    pairs.remove((b, a))
            return pairs

        evl_pairs = get_pairs_from_array(evl_ans)
        ref_pairs = get_pairs_from_array(self.ref_ans)

        correct_share = len(evl_pairs & ref_pairs) / len(ref_pairs)

        return correct_share


class MatchProblem(Problem):
    def __init__(self, ref_ans: str, max_pts: int) -> None:
        super().__init__(ref_ans, max_pts)
        self.ref_ans_table = pd.DataFrame(index=sorted(set(ref_ans)),
                                          columns=range(len(ref_ans)),
                                          data=0)
        for pos, letter in enumerate(self.ref_ans):
            self.ref_ans_table.loc[letter, pos] = 1

    def evaluate_pts(self, evl_ans: str) -> int:
        pts = 0
        for pos, letter in enumerate(evl_ans):
            if letter in self.ref_ans_table.index:
                pts += self.ref_ans_table.loc[letter, pos]
        return pts

    def evaluate(self, evl_ans: str) -> int:
        return round(self.evaluate_pts(evl_ans)/self.evaluate_pts(self.ref_ans) * self.max_pts)


class Evaluator:
    problem_list: list

    def __init__(self, *args: Problem) -> None:
        self.problem_list = args

    def eval_list(self, evl_list: list) -> list:
        pts_list = []
        for ans, pr in zip(evl_list, self.problem_list):
            pts_list.append(pr.evaluate(ans.strip(' ')))
        return pts_list

    def eval_table(self, evl_table: pd.DataFrame) -> pd.DataFrame:
        pts_table = evl_table.copy()
        for row_index in range(pts_table.shape[0]):
            ans = evl_table.iloc[row_index][-len(self.problem_list):]
            pts_table.iloc[row_index, -
                           len(self.problem_list):] = self.eval_list(ans)
        return pts_table
