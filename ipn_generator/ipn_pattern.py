# IPN pattern object

import logging, re, math

class IpnToken:
    def __init__(self, min, max):
        self._value = min
        self.min = min
        self.max = max

    def value(self):
        return self._value

    def incval(self):
        return self._value + 1

    def wrapped(self, val):
        return (self.max is not None) and val > self.max

    def inc(self):
        next = self.incval()
        if self.wrapped(next):
            self._value = self.min
            return True
        self._value = next
        return False

    def __str__(self):
        return str(self.value())

class IpnStatic(IpnToken):
    def __init__(self, val):
        self._value = val
        self.min = val
        self.max = None

    def incval(self):
        return self._value

    def wrapped(self, val):
        return True

    def inc(self):
        return True

class IpnNumeric(IpnToken):
    def __init__(self, digits, min, max):
        self.digits = digits
        self._value = min
        self.min = min
        self.max = max

    def __str__(self):
        return '{:0{width}}'.format(self.value(), width = self.digits)

class IpnAlpha(IpnToken):
    def __init__(self, min, max):
        self._value = min
        self.min = min
        self.max = max

    def incval(self):
        return chr(ord(self._value) + 1)

class IpnOrd(IpnToken):
    def __init__(self, _values):
        self._values = _values
        self._value = 0
        self.min = 0
        self.max = len(self._values) - 1

    def value(self):
        return self._values[self._value]

IPN_RE = re.compile(r"""
      (?P<DIGITS>\{(\d+)\})          # {4}
    | (?P<MIN>\{(\d+)\+\})          # {100+}
    | (?P<DIGNUMRNG>\{(\d+)\:(\d+)\.\.(\d+)\}) # {3:0..999}
    | (?P<ALPHARNG>\[(\w)-(\w)\]) # [A-Z]
    | (?P<ALPHASET>\[(\w+)\])   # [ABC]
    | (?P<LIT1>\(([^()]+)\))          # (IPN-)
    | (?P<LIT2>[^\{\}\[\]\(\)]+)                   # anything else is a literal
    """, re.VERBOSE)

def minDigits(n):
    return int(math.floor(math.log10(n) + 1))

def maxValueForDigits(digits):
    return int(math.pow(10, digits) - 1)

def ipnTokens(pattern):
    for m in IPN_RE.finditer(pattern):
        if m.lastgroup == "DIGITS":
            digits = int(m.group(2))
            tok = IpnNumeric(digits, 0, math.pow(10, digits))
        elif m.lastgroup == "MIN":
            min = int(m.group(4))
            digits = minDigits(min)
            tok = IpnNumeric(digits, min, maxValueForDigits(digits))
        elif m.lastgroup == "DIGNUMRNG":
            digits = int(m.group(6))
            min = int(m.group(7))
            max = int(m.group(8))
            tok = IpnNumeric(digits, min, max)
        elif m.lastgroup == "ALPHARNG":
            min = m.group(10)[0]
            max = m.group(11)[0]
            tok = IpnAlpha(min, max)
        elif m.lastgroup == "LIT1":
            tok = IpnStatic(m.group(15))
        else:
            tok = IpnStatic(m.group(16))
        yield tok

def ipnParse(pattern):
    return list(reversed(list(tok for tok in ipnTokens(pattern))))

class IPN:
    def __init__(self, pattern):
        self.pattern = pattern
        self.tokens = ipnParse(pattern)

    def inc(self):
        carry = True
        for tok in self.tokens:
            if carry:
                carry = tok.inc()
            else:
                break
        return self.tokens

    def __str__(self):
        return ''.join(reversed(list(str(tok) for tok in self.tokens)))

if __name__ == '__main__':
    import sys
    ipn = IPN("AC(01)-[a-b]{4:8..9}")
    print(ipn)
    for i in range(0,4):
        ipn.inc()
        print(ipn)
