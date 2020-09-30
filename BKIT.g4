lexer grammar BKIT;

@lexer::header {
from lexererr import *
}

@lexer::members {
def emit(self):
    tk = self.type
    result = super().emit()
    if tk == self.UNCLOSE_STRING:       
        raise UncloseString(result.text)
    elif tk == self.ILLEGAL_ESCAPE:
        raise IllegalEscape(result.text)
    elif tk == self.ERROR_CHAR:
        raise ErrorToken(result.text)
    elif tk == self.UNTERMINATED_COMMENT:
        raise UnterminatedComment()
    else:
        return result;
}

options{
	language=Python3;
}

fragment LETTER             :  [a-z] ;
fragment DIGIT              :  [0-9] ;
fragment SIGN               :  [+-]? ;
fragment EXPONENT           :  [e](SIGN)(DIGIT)+ ;

IDENT                       :  LETTER (DIGIT | LETTER)* ;
REAL                        :  (SIGN)DIGIT+(([.]DIGIT+(EXPONENT)?) | (EXPONENT)) ;
STRING                      :  '\''('\'\'' | ~('\''))*'\'' ;

WS : [ \t\r\n]+ -> skip ; // skip spaces, tabs, newlines


ERROR_CHAR: .;
UNCLOSE_STRING: .;
ILLEGAL_ESCAPE: .;
UNTERMINATED_COMMENT: .;