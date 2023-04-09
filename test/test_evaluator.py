import unittest
import numpy as np
import pandas as pd
import string
import sys
sys.path.append('../')
from source.evaluator import Problem, SortProblem, MatchProblem, Evaluator

class TestProblem(unittest.TestCase):
    
    def test_evaluate(self):
        problem = Problem(ref_ans='ABC', max_pts=10)
        with self.assertRaises(NotImplementedError):
            problem.evaluate_share('CBA')

    def test_evaluate_share(self):
        problem = Problem(ref_ans='ABC', max_pts=10)
        with self.assertRaises(NotImplementedError):
            problem.evaluate_share('CBA')
            
            
class TestSortProblem(unittest.TestCase):
    
    def test_evaluate_share(self):
        problem = SortProblem(ref_ans='ABCDE', max_pts=10, min_share=0.5)
        self.assertEqual(problem.evaluate_share('ABCDE'), 10/10)
        self.assertEqual(problem.evaluate_share('BACDE'),  9/10)
        self.assertEqual(problem.evaluate_share('BCDEA'),  6/10)
        self.assertEqual(problem.evaluate_share('ADCBE'),  7/10)
        self.assertEqual(problem.evaluate_share('EDCBA'),  0/10)
        # дублирование
    
    def test_evaluate(self):
        problem = SortProblem(ref_ans='ABCDE', max_pts=5, min_share=0.5)
        self.assertEqual(problem.evaluate('ABCDE'), 5)
        self.assertEqual(problem.evaluate('BACDE'), 4)
        self.assertEqual(problem.evaluate('BCDEA'), 1)
        self.assertEqual(problem.evaluate('ADCBE'), 2)
        self.assertEqual(problem.evaluate('EDCBA'), 0)
        
        
class TestMatchProblem(unittest.TestCase):
    
    def test_evaluate(self):
        problem = MatchProblem(ref_ans='ABCDE', max_pts=5)
        self.assertEqual(problem.evaluate('ABCDE'), 5)
        self.assertEqual(problem.evaluate('AACDE'), 3)
        self.assertEqual(problem.evaluate('AXCDE'), 4)
        
    def test_init(self):
        problem = MatchProblem(ref_ans='BAC', max_pts=10)
        expected_table = pd.DataFrame({
            0: [0, 1, 0],
            1: [1, 0, 0],
            2: [0, 0, 1]
        }, index=list('ABC'))
        pd.testing.assert_frame_equal(problem.ref_ans_table, expected_table)

        
class TestEvaluator(unittest.TestCase):
    
    def test_eval_list(self):
        problem1 = SortProblem(ref_ans='ABCDE', max_pts=10, min_share=0.5)
        problem2 = MatchProblem(ref_ans='ABCDE', max_pts=10)
        evl = Evaluator(problem1, problem2)
        ans_list = ['ABDCE', 'ABBCD']
        pts_list = evl.eval_list(ans_list)
        self.assertEqual(pts_list, [8, 2])
        
    def test_eval_table(self):
        problem1 = SortProblem(ref_ans='ABDCE', max_pts=10, min_share=0.5)
        problem2 = SortProblem(ref_ans='ABCDE', max_pts=10, min_share=0.5)
        problem3 = MatchProblem(ref_ans='BACED', max_pts=10)
        evl = Evaluator(problem1, problem2, problem3)
        ans_table = pd.DataFrame({
            1: ['ABCDE', 'BADCE', 'AABCD'],
            2: ['ABCDE', 'BADCE', 'AABCD'],
            3: ['ABCDE', 'BADCE', 'AABCD']
        })
        pts_table = evl.eval_table(ans_table).astype(int)
        expected_table = pd.DataFrame({
            1: [8, 8, 0],
            2: [10, 6, 2],
            3: [2, 4, 2]
        })
        pd.testing.assert_frame_equal(pts_table, expected_table)
