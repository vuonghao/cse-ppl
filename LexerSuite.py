import unittest
from TestUtils import TestLexer

class LexerSuite(unittest.TestCase):
      
    def test_lower_identifier(self):
        """test identifiers"""
        self.assertTrue(TestLexer.checkLexeme("abc","abc,<EOF>",101))

    def test_upper_identifier(self):
        self.assertTrue(TestLexer.checkLexeme("abcXYZ","abc,Error Token X", 102))

    def test_real_1(self):
        self.assertTrue(TestLexer.checkLexeme("1.0", "1.0,<EOF>", 103))

    def test_real_2(self):
        self.assertTrue(TestLexer.checkLexeme("1e-12", "1e-12,<EOF>", 104))

    def test_real_3(self):
        self.assertTrue(TestLexer.checkLexeme("1.0e-12", "1.0e-12,<EOF>", 105))

    def test_real_4(self):
        self.assertTrue(TestLexer.checkLexeme("0.000000001", "0.000000001,<EOF>", 106))

    def test_string_1(self):
        self.assertTrue(TestLexer.checkLexeme("'string'", "'string',<EOF>", 107))

    def test_string_2(self):
        self.assertTrue(TestLexer.checkLexeme("'isn''t'", "'isn''t',<EOF>", 108))

    def test_string_3(self):
        self.assertTrue(TestLexer.checkLexeme("'isn't'","'isn',t,Error Token '",109))

    def test_string_4(self):
        self.assertTrue(TestLexer.checkLexeme("''", "'',<EOF>", 110))    


        

    
