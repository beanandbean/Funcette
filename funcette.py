import operator, sys

baseprio = 50
midbaseprio = 100
prios=("+-", "*/%")
realprios = dict()
for index in xrange(len(prios)):
    for item in prios[index]:
        realprios[item] = midbaseprio * (index + 2)

def realprio(op):
    if op in realprios:
        return realprios[op]
    else:
        return midbaseprio

def isnull(obj):
    return isinstance(obj, FCTNull)

class FCTObj(object):
    def __call__(self, code, env, prio):
        pass

    def __neg__(self):
        return FCTNull()

    def __add__(self, other):
        return FCTNull()

    def __sub__(self, other):
        return FCTNull()

    def __mul__(self, other):
        return FCTNull()

    def __div__(self, other):
        return FCTNull()

    def __mod__(self, other):
        return FCTNull()

    def prio(self):
        return 0

class FCTConst(FCTObj):
    def __call__(self, code, env, prio):
        nex = code.get()
        if nex and isinstance(nex, FCTOperator) and nex.prio() > prio:
            code.pop()
            return nex.asmid(code, env, prio, self)
        else:
            code.reset()
            return self

class FCTNull(FCTConst):
    pass

class FCTString(str, FCTConst):
    def __add__(self, other):
        if isinstance(other, FCTFloat) or isinstance(other, FCTString):
            return FCTString(str(self) + str(other))
        else:
            return FCTNull()

    def __mul__(self, other):
        if isinstance(other, FCTFloat):
            return FCTString(str(self) * int(other))
        else:
            return FCTNull()
    
class FCTFloat(float, FCTConst):
    def __neg__(self):
        return FCTFloat(-float(self))
    
    def __add__(self, other):
        if isinstance(other, FCTFloat):
            return FCTFloat(float(self) + float(other))
        elif isinstance(other, FCTString):
            return FCTString(str(self) + str(other))
        else:
            return FCTNull()

    def __sub__(self, other):
        if isinstance(other, FCTFloat):
            return FCTFloat(float(self) - float(other))
        else:
            return FCTNull()

    def __mul__(self, other):
        if isinstance(other, FCTFloat):
            return FCTFloat(float(self) * float(other))
        elif isinstance(other, FCTString):
            return FCTString(int(self) * str(other))
        else:
            return FCTNull()

    def __div__(self, other):
        if isinstance(other, FCTFloat) and float(other) != 0:
            return FCTFloat(float(self) / float(other))
        else:
            return FCTNull()

    def __mod__(self, other):
        if isinstance(other, FCTFloat) and float(other) != 0:
            return FCTFloat(float(self) % float(other))
        else:
            return FCTNull()

class FCTFunc(FCTObj):
    def __init__(self, func, argc, prio = midbaseprio, needleft = False):
        self.func = func
        self.argc = argc
        self.args = []
        self.prio = baseprio
        self.realprio = prio
        self.needleft = needleft
        self.blankleft = needleft

    def asmid(self, code, env, prio, obj):
        partial = FCTFunc(self.func, self.argc, self.realprio)
        if self.needleft:
            partial.args = [obj] + self.args
        else:
            partial.args = self.args + [obj]
        partial.prio = self.realprio
        return partial(code, env, prio)

    def truncmid(self, code, env, prio):
        partial = FCTFunc(self.func, self.argc, self.realprio, True)
        partial.args = self.args
        return partial(code, env, prio)
    
    def __call__(self, code, env, prio):
        if len(self.args) == self.argc:
            res = self.func(*self.args)
            return res(code, env, prio)
        else:
            nex = code.pop()
            if nex and isinstance(nex, FCTOperator) and nex.prio() > prio:
                return nex.asmid(code, env, prio, self)
            elif nex:
                res = nex(code, env, self.prio)
                partial = FCTFunc(self.func, self.argc, self.realprio, self.needleft)
                if self.needleft:
                    if self.blankleft and self.argc - len(self.args) == 1:
                        partial.args = [res] + self.args
                        partial.needleft = False
                        partial.blankleft = False
                    else:
                        partial.args = self.args + [res]
                elif self.blankleft:
                    partial.args = [res] + self.args
                else:
                    partial.args = self.args + [res]
                return partial(code, env, prio)
            else:
                partial = FCTFunc(self.func, self.argc, self.realprio)
                partial.args = self.args
                partial.blankleft = self.blankleft
                return partial

class FCTIdentifier(FCTObj):
    def __init__(self, identifier):
        self.identifier = identifier

    def __call__(self, code, env, prio):
        obj = env[self.identifier]
        return obj(code, env, prio)

    def __str__(self):
        return "<%s>" % self.identifier

    def __repr__(self):
        return "<%s>" % self.identifier

    def prio(self):
        return baseprio

class FCTOperator(FCTIdentifier):
    def __str__(self):
        return "`%s`" % self.identifier

    def __repr__(self):
        return "`%s`" % self.identifier

    def asmid(self, code, env, prio, obj):
        obj1 = env[self.identifier]
        if not isnull(obj1):
            return obj1.asmid(code, env, prio, obj)
        else:
            return FCTNull()

    def __call__(self, code, env, prio):
        obj1 = env[self.identifier]
        if not isnull(obj1):
            return obj1.truncmid(code, env, prio)
        else:
            return FCTNull()

    def prio(self):
        return realprio(self.identifier)

class FCTBracket(FCTObj):
    def __init__(self):
        self.code = FCTCode()

    def __str__(self):
        res = "( "
        for item in self.code:
            res += str(item) + " "
        res += ")"
        return res

    def __repr__(self):
        res = "( "
        for item in self.code:
            res += repr(item) + " "
        res += ")"
        return res

    def __call__(self, code, env, prio):
        res = FCTNull()
        if self.code:
            res = self.code.pop()(self.code, env, 0)
        return res(code, env, prio)
            

glob = dict()

def FCTFUNC(argc, prio = midbaseprio, needleft = False):
    def fctfunc(func):
        return FCTFunc(func, argc, prio, needleft)
    return fctfunc

@FCTFUNC(1)
def print_(obj):
    print obj,
    return print_
glob["print"] = print_

@FCTFUNC(1)
def println_(obj):
    print obj
    return println_
glob["println"] = println_

glob["neg"] = FCTFUNC(1)(operator.neg)

def midCons(func, argc, op):
    return (FCTFunc(func, argc, midbaseprio), FCTFunc(func, argc, realprio(op), True))

glob["add"] = glob["+"] = FCTFunc(operator.add, 2, realprio("+"))
glob["sub"] = glob["-"] = FCTFunc(operator.sub, 2, realprio("-"))
glob["mul"] = glob["*"] = FCTFunc(operator.mul, 2, realprio("*"))
glob["div"] = glob["/"] = FCTFunc(operator.div, 2, realprio("/"))
glob["mod"] = glob["%"] = FCTFunc(operator.mod, 2, realprio("%"))

class FCTEnv(dict):
    def __getitem__(self, key):
        global glob
        if key in self:
            return dict.__getitem__(self, key)
        elif key in glob:
            return glob[key]
        else:
            return FCTNull()

globenv = FCTEnv()

class FCTCode(list):
    def __init__(self, *args, **kwds):
        list.__init__(self, *args, **kwds)
        self.popid = 0
        self.getid = 0

    def pop(self):
        if self.popid < len(self):
            obj = self[self.popid]
            self.popid += 1
            self.reset()
            return obj
        else:
            return None

    def get(self):
        if self.getid < len(self):
            obj = self[self.getid]
            self.getid += 1
            return obj
        else:
            return None

    def reset(self):
        self.getid = self.popid

STATE_NORMAL = "NORMAL"
STATE_SINGLE_QUOTE = "SINGLE_QUOTE"
STATE_DOUBLE_QUOTE = "DOUBLE_QUOTE"
STATE_IDENTIFIER = "IDENTIFIER"
STATE_NUMBER = "NUMBER"
STATE_COMMENT = "COMMENT"
STATE_MID_IDENTIFIER = "MID_IDENTIFIER"

if len(sys.argv) > 1:
    f = open(sys.argv[1])
    lines = f.readlines()
    for text in lines:
        code = [FCTCode()]
        curr_state = STATE_NORMAL
        index = 0
        while index < len(text):
            ch = text[index]
            if curr_state == STATE_NORMAL:
                if ch == "'":
                    curr_state = STATE_SINGLE_QUOTE
                    buf = ""
                    slash = False
                elif ch == '"':
                    curr_state = STATE_DOUBLE_QUOTE
                    buf = ""
                    slash = False
                elif ch.isalpha():
                    curr_state = STATE_IDENTIFIER
                    buf = ch
                elif ch.isdigit():
                    curr_state = STATE_NUMBER
                    buf = ch
                    hasdot = False
                elif ch == "#":
                    curr_state = STATE_COMMENT
                elif ch == "`":
                    curr_state = STATE_MID_IDENTIFIER
                    buf = ""
                elif ch.isspace():
                    pass
                elif ch == "(":
                    bracket = FCTBracket()
                    code[-1].append(bracket)
                    code.append(bracket.code)
                elif ch == ")":
                    code.pop()
                else:
                    code[-1].append(FCTOperator(ch))
            elif curr_state == STATE_SINGLE_QUOTE:
                if slash:
                    if ch == "n":
                        buf += "\n"
                    else:
                        buf += ch
                    slash = False
                else:
                    if ch == "'":
                        curr_state = STATE_NORMAL
                        code[-1].append(FCTString(buf))
                    elif ch == "\\":
                        slash = True
                    else:
                        buf += ch
            elif curr_state == STATE_DOUBLE_QUOTE:
                if slash:
                    if ch == "n":
                        buf += "\n"
                    elif ch == "t":
                        buf += "\t"
                    else:
                        buf += ch
                    slash = False
                else:
                    if ch == '"':
                        curr_state = STATE_NORMAL
                        code[-1].append(FCTString(buf))
                    elif ch == "\\":
                        slash = True
                    else:
                        buf += ch
            elif curr_state == STATE_IDENTIFIER:
                if ch.isalnum() or ch == "_":
                    buf += ch
                elif ch == "#":
                    curr_state = STATE_COMMENT
                    code[-1].append(FCTIdentifier(buf))
                elif ch.isspace():
                    curr_state = STATE_NORMAL
                    code[-1].append(FCTIdentifier(buf))
                else:
                    curr_state = STATE_NORMAL
                    code[-1].append(FCTIdentifier(buf))
                    index -= 1
            elif curr_state == STATE_NUMBER:
                if ch.isdigit():
                    buf += ch
                elif ch == ".":
                    if hasdot:
                        curr_state = STATE_NORMAL
                        code[-1].append(FCTFloat(buf))
                        index -= 1
                    else:
                        buf += ch
                        hasdot = True
                elif ch == "#":
                    curr_state = STATE_COMMENT
                    code[-1].append(FCTFloat(buf))
                elif ch.isspace():
                    curr_state = STATE_NORMAL
                    code[-1].append(FCTFloat(buf))
                else:
                    curr_state = STATE_NORMAL
                    code[-1].append(FCTFloat(buf))
                    index -= 1
            elif curr_state == STATE_MID_IDENTIFIER:
                if ch == "`":
                    curr_state = STATE_NORMAL
                    code[-1].append(FCTOperator(buf))
                else:
                    buf += ch
            index += 1
        if curr_state == STATE_IDENTIFIER:
            code[-1].append(FCTIdentifier(buf))
        elif curr_state == STATE_NUMBER:
            code[-1].append(FCTFloat(buf))
        if code[0]:
            code[0].pop()(code[0], globenv, 0)
else:
    print "Please run the interpreter with a Funcette source file!"
