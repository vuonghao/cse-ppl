#########################################################
#########################################################

from StaticError import *
from Utils import Utils
from Visitor import *
from AST import *
from functools import reduce
import sys

sys.path.append('../../../../target/main/mp/parser')
sys.path.append('../utils')


#########################################################
#########################################################


class MType:
    """
    MType: type of function declaration
    partype: list(Type) - params type
    rettype: Type       - return type
    """

    def __init__(self, partype, rettype):
        self.partype = partype
        self.rettype = rettype

    def __str__(self):
        return 'MType([' + ','.join([str(i) for i in self.partype]) + '],' + str(self.rettype) + ')'

class ExpUtils:
    @staticmethod
    def isNumberType(expType):
        return type(expType) in [IntType, FloatType]

    @staticmethod
    def isNaNType(expType):
        return not ExpUtils.isNumberType(expType)

    @staticmethod
    def isOpForNumber(operator):
        return str(operator).lower() in ['+', '-', '*', '/', 'div', 'mod', '<>', '=', '>', '<', '>=', '<=']

    @staticmethod
    def mergeNumberType(lType, rType):
        return FloatType() if FloatType in [type(x) for x in [lType, rType]] else IntType()


class Symbol:
    """
    name: string
    mtype: MType | IntType | FloatType | StringType | BoolType | ArrayType
    value: ???
    kind: Function() | Procedure() | Parameter() | Variable()
    """

    # Default Declare Type is Function Declare - kind Function
    def __init__(self, name, mtype, value=None, kind=Function()):
        self.name = name
        self.mtype = mtype
        self.value = value
        self.kind = kind

    def __str__(self):
        return 'Symbol(' + self.name + ',' + str(self.mtype) + ',' + str(self.kind) + ')'

    def getKind(self):
        return self.kind if self.isFunc() else Identifier()

    def toTuple(self):
        return (self.name, type(self.getKind()))

    def toTuple_2(self):
        return (self.name, str(self.mtype))

    def isVar(self):
        return type(self.mtype) is not MType

    def isFunc(self):
        return type(self.mtype) is MType

    def toFunc(self):
        self.kind = Function()
        return self

    def toProc(self):
        self.kind = Procedure()
        return self

    def toParam(self):
        self.kind = Parameter()
        return self

    def toVar(self):
        self.kind = Variable()
        return self

    # compare function between 2 instances
    @staticmethod
    def cmp(symbol):
        return symbol.name

    @staticmethod
    def fromVarDecl(decl):
        return Symbol(decl.variable.name, decl.varType, kind=Variable())

    @staticmethod
    def fromFuncDecl(decl):
        kind = Procedure() if type(decl.returnType) is VoidType else Function()
        paramType = [x.varType for x in decl.param]
        return Symbol(decl.name.name, MType(paramType, decl.returnType), kind=kind)

    @staticmethod
    def fromDecl(decl):
        return Symbol.fromVarDecl(decl) if type(decl) is VarDecl else Symbol.fromFuncDecl(decl)

class Scope:
    @staticmethod
    def start(section):
        print("================   " + section + "   ================")

    @staticmethod
    def end():
        print("=====================================================")

    @staticmethod
    def filterVarDecl(listSymbols):
        return [x for x in listSymbols if x.isVar()]

    @staticmethod
    def filterFuncDecl(listSymbols):
        return [x for x in listSymbols if x.isFunc()]

    @staticmethod
    def filterId(listSymbols, id):
        f = [x for x in listSymbols if x.name == id.name]
        return f[0] if len(f) > 0 else None

    @staticmethod
    def isExisten(listSymbols, symbol):
        return len([x for x in listSymbols if x.name == symbol.name]) > 0

    @staticmethod
    def merge(currentScope, comingScope):
        return reduce(lambda lst, sym: lst if Scope.isExisten(lst, sym) else lst+[sym], currentScope, comingScope)

    @staticmethod
    def log(scope):
        [print(x) for x in scope]

class Checker:

    utils = Utils()

    @staticmethod
    def checkRedeclared(currentScope, listNewSymbols):
        # Return merged scope
        newScope = currentScope
        for x in listNewSymbols:
            f = Checker.utils.lookup(x.name, newScope, Symbol.cmp)
            if f is not None:
                raise Redeclared(x.kind, x.name)
            newScope.append(x)
        return newScope

    @staticmethod
    def checkUndeclared(visibleScope, name, kind):
        # Return Symbol declared in scope
        res = Checker.utils.lookup((name, type(kind)), visibleScope, lambda x: x.toTuple())
        if res is None:
            raise Undeclared(kind, name)
        return res

    @staticmethod
    def matchArrayType(a, b):
        return a.lower == b.lower and a.upper == b.upper and type(a.eleType) == type(b.eleType)

    @staticmethod
    def matchType(patternType, paramType):
        # Handle Array Type
        if ArrayType in [type(x) for x in [patternType, paramType]]:
            if type(patternType) != type(paramType): return False
            return Checker.matchArrayType(patternType, paramType)

        # Handle Primitive Types
        if type(patternType) == type(paramType): return True
        if type(patternType) is FloatType and type(paramType) is IntType: return True
        return False

    @staticmethod
    def checkParamType(pattern, params):
        if len(pattern) != len(params): return False
        return all([Checker.matchType(a, b) for a, b in zip(pattern, params)])

    @staticmethod
    def handleReturnStmts(stmts):
        # only scalar return type of statements
        # stmts: (stmt, [type]) type: None, VoidType, (...)Type, Break
        for i in range(0, len(stmts)-1):
            if Checker.isStopTypeStatment(stmts[i][1]):
                raise UnreachableStatement(stmts[i+1][0])
        return None if stmts == [] else stmts[-1][1]

    @staticmethod
    def isReturnTypeFunction(retType):
        return type(retType) in [IntType, FloatType, BoolType, StringType, ArrayType]

    @staticmethod
    def isReturnTypeProcedure(retType):
        return type(retType) is VoidType

    @staticmethod
    def isReturnType(retType):
        return Checker.isReturnTypeFunction(retType) or Checker.isReturnTypeProcedure(retType)

    @staticmethod
    def isStopTypeStatment(retType):
        return Checker.isReturnType(retType) or type(retType) in [Break]

class Graph:
    link = {}

    @staticmethod
    def add(u, v):
        if type(Graph.link[u]) != list: Graph.link[u] = []
        if v != u and v not in Graph.link[u]: link[u].append(v)

class StaticChecker(BaseVisitor, Utils):

    # Global Environement - Built-in Functions - Default is Function
    global_envi = [
        Symbol("getInt", MType([], IntType())),
        Symbol("getFloat", MType([], FloatType())),
        Symbol("putInt", MType([IntType()], VoidType())),
        Symbol("putIntLn", MType([IntType()], VoidType())),
        Symbol("putFloat", MType([FloatType()], VoidType())),
        Symbol("putFloatLn", MType([FloatType()], VoidType())),
        Symbol("putBool", MType([BoolType()], VoidType())),
        Symbol("putBoolLn", MType([BoolType()], VoidType())),
        Symbol("putString", MType([StringType()], VoidType())),
        Symbol("putStringLn", MType([StringType()], VoidType())),
        Symbol("putLn", MType([], VoidType()))
    ]

    def __init__(self, ast):
        self.ast = ast

    def check(self):
        return self.visit(self.ast, StaticChecker.global_envi)

    def visitProgram(self, ast: Program, scope):
        # Return []
        Scope.start("Program")
        symbols = [Symbol.fromDecl(x) for x in ast.decl]
        # Check Redeclared variable/function/procedure
        scope = Checker.checkRedeclared(scope, symbols)

        # Check entry procedure
        entryPoint = Symbol('main', MType([], VoidType()), kind=Procedure())
        res = self.lookup(entryPoint.toTuple_2(), symbols, lambda x: x.toTuple_2())
        if res is None: raise NoEntryPoint()

        # Init graph
        listFuncDecl = ["main"] + [x.name.name for x in ast.decl if type(x) is FuncDecl]
        for x in listFuncDecl: Graph.link[x] = []
        
        # Visit children
        [self.visit(x, scope) for x in ast.decl]

        # Check unreachable function / procedure
        for x in listFuncDecl:
            res = self.lookup(x.toTuple_2(), StaticChecker.invokedFunctions, lambda x: x.toTuple_2())
            if res: raise Unreachable(x.getKind(), x.name)

        Scope.end()
        return []

    def visitFuncDecl(self, ast: FuncDecl, scope):
        # Return Symbol
        Scope.start("FuncDecl")
        listParams = [self.visit(x, scope).toParam() for x in ast.param]
        listLocalVar = [self.visit(x, scope).toVar() for x in ast.local]
        listNewSymbols = listParams + listLocalVar
        # Check Redeclared parameter/variable
        localScope = Checker.checkRedeclared([], listNewSymbols)
        # new scope for statements
        newScope = Scope.merge(scope, localScope)
        # Scope.log(newScope)

        # params: (scope, retType, inLoop, funcName)
        stmts = [self.visit(x, (newScope, ast.returnType, False, ast.name.name)) for x in ast.body]

        # Type of return result
        retType = Checker.handleReturnStmts(stmts)
        print(retType)

        # Function not return
        if Checker.isReturnTypeFunction(ast.returnType) and not Checker.isReturnTypeFunction(retType):
            raise FunctionNotReturn(ast.name.name)

        # Update Graph


        Scope.end()
        return Symbol.fromDecl(ast)

    def visitVarDecl(self, ast, scope):
        # Return Symbol
        return Symbol.fromDecl(ast)

# Visit Statements -> use params (scope, retType, inLoop, funcName)
# Return tuple (Statement, Type of return type)

    def visitAssign(self, ast: Assign, params):
        # Return None
        scope = params[0]
        retType = params[1]
        Scope.start("Assign")
        # Scope.log(scope)
        lhsType = self.visit(ast.lhs, scope)
        expType = self.visit(ast.exp, scope)
        if type(lhsType) in [ArrayType, VoidType] or not Checker.matchType(lhsType, expType):
            raise TypeMismatchInStatement(ast)
        Scope.end()
        return (ast, None)

    def visitWith(self, ast: With, params):
        # Return Type of return result
        scope = params[0]
        retType = params[1]
        inLoop = params[2]
        Scope.start("With")
        listVar = [self.visit(x, scope).toVar() for x in ast.decl]
        # Check Redeclared variable
        localScope = Checker.checkRedeclared([], listVar)
        # new scope for statements
        newScope = Scope.merge(scope, localScope)
        # Scope.log(newScope)

        stmts = [self.visit(x, (newScope, retType, inLoop)) for x in ast.stmt]

        Scope.end()
        return (ast, Checker.handleReturnStmts(stmts))

    def visitIf(self, ast: If, params):
        # Return Type of return result
        scope = params[0]
        retType = params[1]
        Scope.start("If")
        condType = self.visit(ast.expr, scope)
        if type(condType) is not BoolType:
            raise TypeMismatchInStatement(ast)
        stmts1 = [self.visit(x, params) for x in ast.thenStmt]
        stmts2 = [self.visit(x, params) for x in ast.elseStmt]
        ret1 = Checker.handleReturnStmts(stmts1)
        ret2 = Checker.handleReturnStmts(stmts2)
        print(ret1, ret2)
        Scope.end()
        if ret1 is None or ret2 is None: return (ast, None)
        # in case 2 flows return or break -> unreachable statements
        return (ast, ret1)

    def visitFor(self, ast: For, params):
        # Return type of return result
        scope = params[0]
        retType = params[1]
        Scope.start("For")
        idSymbol = Checker.checkUndeclared(scope, ast.id.name, Identifier())
        exp1Type = self.visit(ast.expr1, scope)
        exp2Type = self.visit(ast.expr2, scope)
        # print(idSymbol, exp1Type, exp2Type)
        if type(exp1Type) is not IntType or \
                type(exp2Type) is not IntType or \
                type(idSymbol.mtype) is not IntType:
            raise TypeMismatchInStatement(ast)

        stmts = [self.visit(x, (scope, retType, True)) for x in ast.loop]
        Scope.end()
        return (ast, Checker.handleReturnStmts(stmts))

    def visitWhile(self, ast: While, params):
        # Return type of return result
        scope = params[0]
        retType = params[1]
        Scope.start("While")
        condType = self.visit(ast.exp, scope)
        if type(condType) is not BoolType:
            raise TypeMismatchInStatement(ast)
        stmts = [self.visit(x, (scope, retType, True)) for x in ast.sl]
        Scope.end()
        return (ast, Checker.handleReturnStmts(stmts))

    def visitContinue(self, ast, params):
        # Return None
        inLoop = params[2]
        if not inLoop:
            raise ContinueNotInLoop()
        return (ast, None)

    def visitBreak(self, ast, params):
        # Return type Break
        inLoop = params[2]
        if not inLoop:
            raise BreakNotInLoop()
        return (ast, Break())

    def visitReturn(self, ast: Return, params):
        # Return type of return result
        scope = params[0]
        retType = params[1]
        if retType is VoidType and ast.expr:
            raise TypeMismatchInStatement(ast)
        ret = self.visit(ast.expr, scope) if ast.expr else VoidType()
        print(ret)
        if not Checker.matchType(retType, ret):
            raise TypeMismatchInStatement(ast)
        return (ast, ret)

    def visitCallStmt(self, ast: CallStmt, params):
        # Return None
        scope = params[0]
        Scope.start("CallStmt")
        # Check Undeclared Procedure
        symbol = Checker.checkUndeclared(scope, ast.method.name, Procedure())

        paramType = [self.visit(x, scope) for x in ast.param]
        # Scope.log(symbol.mtype.partype)
        # Scope.log(paramType)
        if not Checker.checkParamType(symbol.mtype.partype, paramType):
            raise TypeMismatchInExpression(ast)

        Scope.end()
        return (ast, None)


# Visit Expression -> use scope
# Return Type

    def visitBinaryOp(self, ast: BinaryOp, scope):
        # Return Type
        Scope.start("BinaryOp")
        lType = self.visit(ast.left, scope)
        rType = self.visit(ast.right, scope)
        op = str(ast.op).lower()
        Scope.end()
        if ExpUtils.isOpForNumber(op):  # for number
            if ExpUtils.isNaNType(lType) or ExpUtils.isNaNType(rType):
                raise TypeMismatchInExpression(ast)
            if str(op).lower() in ['div', 'mod']:
                if type(lType) is FloatType or type(rType) is FloatType:
                    raise TypeMismatchInExpression(ast)
                return IntType
            if op in ['+', '-', '*']: return ExpUtils.mergeNumberType(lType, rType)
            if op == '/': return FloatType()
            return BoolType()  # = <> >= ...
        else:  # for logical
            if type(lType) is not BoolType or type(rType) is not BoolType:
                raise TypeMismatchInExpression(ast)
            return BoolType()

    def visitUnaryOp(self, ast: UnaryOp, scope):
        # Return Type, op: ['-', 'not']
        Scope.start("UnaryOp")
        expType = self.visit(ast.body, scope)
        if (ast.op == '-' and ExpUtils.isNaN(expType)) or (str(ast.op).lower() == 'not' and type(expType) is not BoolType):
            raise TypeMismatchInExpression(ast)
        Scope.end()
        return expType

    def visitCallExpr(self, ast: CallExpr, scope):
        # Return Type
        Scope.start("CallExpr")
        symbol = Checker.checkUndeclared(scope, ast.method.name, Function())
        paramType = [self.visit(x, scope) for x in ast.param]
        # Scope.log(symbol.mtype.partype)
        # Scope.log(paramType)
        if not Checker.checkParamType(symbol.mtype.partype, paramType):
            raise TypeMismatchInExpression(ast)

        Scope.end()
        return symbol.mtype.rettype

    def visitId(self, ast: Id, scope):
        # Return Type
        Scope.start("Id")
        # Scope.log(scope)
        symbol = Checker.checkUndeclared(scope, ast.name, Identifier())
        Scope.end()
        return symbol.mtype

    def visitArrayCell(self, ast: ArrayCell, scope):
        # Return Type
        Scope.start("ArrayCell")
        # arr[idx] - a[1], foo()["bar" + goo()]
        arrType = self.visit(ast.arr)  # type of arr
        idxType = self.visit(ast.idx)  # type of idx
        if type(idxType) is not IntType or type(arrType) is not ArrayType:
            raise TypeMismatchInExpression(ast)
        Scope.end()
        return arrType.eleType

    # Visit Literal Values
    # Return Type of Literal
    def visitIntLiteral(self, ast, scope):
        return IntType()

    def visitFloatLiteral(self, ast, scope):
        return FloatType()

    def visitBooleanLiteral(self, ast, scope):
        return BoolType()

    def visitStringLiteral(self, ast, scope):
        return StringType()

    # Visit Types

    def visitIntType(self, ast, scope):
        return IntType()

    def visitFloatType(self, ast, scope):
        return FloatType()

    def visitBoolType(self, ast, scope):
        return BoolType()

    def visitStringType(self, ast, scope):
        return StringType()

    def visitVoidType(self, ast, scope):
        return VoidType()

    def visitArrayType(self, ast: ArrayType, scope):
        return ArrayType(ast.lower, ast.upper, ast.eleType)
