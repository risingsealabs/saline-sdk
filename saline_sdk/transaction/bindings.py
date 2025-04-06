# Auto-generated - do not edit manually

import json
import string
import typing
from blspy import G1Element, G2Element
from enum import Enum
from numpy import uint64, float64
from typing import Optional
from uuid import UUID

class NonEmpty[T]():
  def __init__(self, head: T, tail:list[T]):
    self.list = [head] + tail

  @staticmethod
  def from_list(elements: list[T]):
    match elements:
      case []: raise ValueError
      case _: return NonEmpty(elements[0], elements[1:])

  @staticmethod
  def to_json(x: 'NonEmpty'):
    if (not isinstance(x,NonEmpty)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(NonEmpty)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    return x.list

  @staticmethod
  def from_json(x):
    return NonEmpty.from_list(x)


def dumps(x):
  return json.dumps(x, separators=(',', ':'))

def loads(x):
  return json.loads(x)


class Relation(Enum):
  EQ = 0
  LT = 1
  LE = 2
  GT = 3
  GE = 4

  @staticmethod
  def from_json(s):
    return Relation[s]

  @staticmethod
  def to_json(x: 'Relation'):
    if (not isinstance(x,Relation)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Relation)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    return x.name


class Token(Enum):
  BTC = 0
  ETH = 1
  USDC = 2
  USDT = 3
  SALT = 4

  @staticmethod
  def from_json(s):
    return Token[s]

  @staticmethod
  def to_json(x: 'Token'):
    if (not isinstance(x,Token)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Token)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    return x.name


class Arithmetic(Enum):
  Add = 0
  Div = 1
  Mul = 2
  Sub = 3

  @staticmethod
  def from_json(s):
    return Arithmetic[s]

  @staticmethod
  def to_json(x: 'Arithmetic'):
    if (not isinstance(x,Arithmetic)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Arithmetic)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    return x.name


class VariableTag(Enum):
  Address = 0
  Amount = 1
  Count = 2
  List = 3

  @staticmethod
  def from_json(s):
    return VariableTag[s]

  @staticmethod
  def to_json(x: 'VariableTag'):
    if (not isinstance(x,VariableTag)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(VariableTag)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    return x.name


class Variable():
  def __init__(self, kind: VariableTag, name: str):
    super().__init__()
    self.kind = kind
    self.name = name

  @staticmethod
  def from_json(d):
    return Variable(VariableTag.from_json(d["kind"]), d["name"])

  @staticmethod
  def to_json(x: 'Variable'):
    if (not isinstance(x,Variable)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Variable)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["kind"] = VariableTag.to_json(x.kind)
    d["name"] = x.name
    return d


# Witness types

class Witness():
  def __init__(self):
    pass

  @staticmethod
  def from_json(d):
    match d["tag"]:
      case "AllW":
        return AllW.from_json(d)
      case "AnyW":
        return AnyW.from_json(d)
      case "AutoW":
        return AutoW.from_json(d)

  @staticmethod
  def to_json(x: 'Witness'):
    if (not isinstance(x,Witness)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Witness)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    match x:
      case AllW():
        d = {"tag" : "AllW"} | AllW.to_json(x)
        return dict(sorted(d.items()))
      case AnyW():
        d = {"tag" : "AnyW"} | AnyW.to_json(x)
        return dict(sorted(d.items()))
      case AutoW():
        d = {"tag" : "AutoW"} | AutoW.to_json(x)
        return dict(sorted(d.items()))


class AllW(Witness):
  def __init__(self, children: list[Witness]):
    super().__init__()
    self.children = children

  @staticmethod
  def from_json(d):
    return AllW(list(map(Witness.from_json, d["children"])))

  @staticmethod
  def to_json(x: 'AllW'):
    if (not isinstance(x,AllW)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(AllW)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["children"] = list(map(Witness.to_json, x.children))
    return d


class AnyW(Witness):
  def __init__(self, children: dict[uint64,Witness]):
    super().__init__()
    self.children = children

  @staticmethod
  def from_json(d):
    return AnyW(dict(d["children"]))

  @staticmethod
  def to_json(x: 'AnyW'):
    if (not isinstance(x,AnyW)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(AnyW)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["children"] = list(x.children.items())
    return d


class AutoW(Witness):
  def __init__(self):
    pass

  @staticmethod
  def from_json(d):
    return AutoW()

  @staticmethod
  def to_json(x: 'AutoW'):
    if (not isinstance(x,AutoW)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(AutoW)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    return d


# Expr types

class Expr():
  def __init__(self):
    pass

  @staticmethod
  def from_json(d):
    match d["tag"]:
      case "Lit":
        return Lit.from_json(d)
      case "Balance":
        return Balance.from_json(d)
      case "Receive":
        return Receive.from_json(d)
      case "Send":
        return Send.from_json(d)
      case "Var":
        return Var.from_json(d)
      case "Arithmetic2":
        return Arithmetic2.from_json(d)

  @staticmethod
  def to_json(x: 'Expr'):
    if (not isinstance(x,Expr)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Expr)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    match x:
      case Lit():
        d = {"tag" : "Lit"} | Lit.to_json(x)
        return dict(sorted(d.items()))
      case Balance():
        d = {"tag" : "Balance"} | Balance.to_json(x)
        return dict(sorted(d.items()))
      case Receive():
        d = {"tag" : "Receive"} | Receive.to_json(x)
        return dict(sorted(d.items()))
      case Send():
        d = {"tag" : "Send"} | Send.to_json(x)
        return dict(sorted(d.items()))
      case Var():
        d = {"tag" : "Var"} | Var.to_json(x)
        return dict(sorted(d.items()))
      case Arithmetic2():
        d = {"tag" : "Arithmetic2"} | Arithmetic2.to_json(x)
        return dict(sorted(d.items()))

  def __add__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Arithmetic2(self, Arithmetic.Add, other)

  def __radd__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Arithmetic2(other, Arithmetic.Add, self)

  def __mul__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Arithmetic2(self, Arithmetic.Mul, other)

  def __rmul__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Arithmetic2(other, Arithmetic.Mul, self)

  def __sub__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Arithmetic2(self, Arithmetic.Sub, other)

  def __rsub__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Arithmetic2(other, Arithmetic.Sub, self)

  def __div__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Arithmetic2(self, Arithmetic.Div, other)

  def __rdiv__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Arithmetic2(other, Arithmetic.Div, self)

  def __gt__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Restriction(self, Relation.GT, other)

  def __lt__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Restriction(self, Relation.LT, other)

  def __ge__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Restriction(self, Relation.GE, other)

  def __le__(self, other):
    if (isinstance(other, int) | isinstance(other, float)):
      other = Lit(other)
    return Restriction(self, Relation.LE, other)


class Lit(Expr):
  def __init__(self, value: typing.Any):
    super().__init__()
    self.value = value

  @staticmethod
  def from_json(d):
    return Lit(d["value"])

  @staticmethod
  def to_json(x: 'Lit'):
    if (not isinstance(x,Lit)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Lit)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["value"] = x.value
    return d


class Balance(Expr):
  def __init__(self, token: Token):
    super().__init__()
    self.token = token

  @staticmethod
  def from_json(d):
    return Balance(Token.from_json(d["token"]))

  @staticmethod
  def to_json(x: 'Balance'):
    if (not isinstance(x,Balance)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Balance)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["token"] = Token.to_json(x.token)
    return d


class Receive(Expr):
  def __init__(self, flow: 'Flow'):
    super().__init__()
    self.flow = flow

  @staticmethod
  def from_json(d):
    return Receive(Flow.from_json(d["flow"]))

  @staticmethod
  def to_json(x: 'Receive'):
    if (not isinstance(x,Receive)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Receive)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["flow"] = Flow.to_json(x.flow)
    return d


class Send(Expr):
  def __init__(self, flow: 'Flow'):
    super().__init__()
    self.flow = flow

  @staticmethod
  def from_json(d):
    return Send(Flow.from_json(d["flow"]))

  @staticmethod
  def to_json(x: 'Send'):
    if (not isinstance(x,Send)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Send)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["flow"] = Flow.to_json(x.flow)
    return d


class Var(Expr):
  def __init__(self, var: Variable):
    super().__init__()
    self.var = var

  @staticmethod
  def from_json(d):
    return Var(Variable.from_json(d["var"]))

  @staticmethod
  def to_json(x: 'Var'):
    if (not isinstance(x,Var)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Var)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["var"] = Variable.to_json(x.var)
    return d


class Arithmetic2(Expr):
  def __init__(self, lhs: Expr, operation: Arithmetic, rhs: Expr):
    super().__init__()
    self.lhs = lhs
    self.operation = operation
    self.rhs = rhs

  @staticmethod
  def from_json(d):
    return Arithmetic2(Expr.from_json(d["lhs"]), Arithmetic.from_json(d["operation"]), Expr.from_json(d["rhs"]))

  @staticmethod
  def to_json(x: 'Arithmetic2'):
    if (not isinstance(x,Arithmetic2)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Arithmetic2)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["lhs"] = Expr.to_json(x.lhs)
    d["operation"] = Arithmetic.to_json(x.operation)
    d["rhs"] = Expr.to_json(x.rhs)
    return d


class Flow():
  def __init__(self, target: Optional[Expr], token: Token):
    super().__init__()
    self.target = target
    self.token = token

  @staticmethod
  def from_json(d):
    return Flow(None if d["target"] == None else Expr.from_json(d["target"]), Token.from_json(d["token"]))

  @staticmethod
  def to_json(x: 'Flow'):
    if (not isinstance(x,Flow)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Flow)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["target"] = None if x.target == None else Expr.to_json(x.target)
    d["token"] = Token.to_json(x.token)
    return d


# Intent types

class Intent():
  def __init__(self):
    pass

  @staticmethod
  def from_json(d):
    match d["tag"]:
      case "All":
        return All.from_json(d)
      case "Any":
        return Any.from_json(d)
      case "Restriction":
        return Restriction.from_json(d)
      case "Finite":
        return Finite.from_json(d)
      case "Temporary":
        return Temporary.from_json(d)
      case "Signature":
        return Signature.from_json(d)

  @staticmethod
  def to_json(x: 'Intent'):
    if (not isinstance(x,Intent)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Intent)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    match x:
      case All():
        d = {"tag" : "All"} | All.to_json(x)
        return dict(sorted(d.items()))
      case Any():
        d = {"tag" : "Any"} | Any.to_json(x)
        return dict(sorted(d.items()))
      case Restriction():
        d = {"tag" : "Restriction"} | Restriction.to_json(x)
        return dict(sorted(d.items()))
      case Finite():
        d = {"tag" : "Finite"} | Finite.to_json(x)
        return dict(sorted(d.items()))
      case Temporary():
        d = {"tag" : "Temporary"} | Temporary.to_json(x)
        return dict(sorted(d.items()))
      case Signature():
        d = {"tag" : "Signature"} | Signature.to_json(x)
        return dict(sorted(d.items()))

  def __and__(self, other):
    return All([self, other])

  def __or__(self, other):
    return Any(1, [self, other])


class All(Intent):
  def __init__(self, children: list[Intent]):
    super().__init__()
    self.children = children

  @staticmethod
  def from_json(d):
    return All(list(map(Intent.from_json, d["children"])))

  @staticmethod
  def to_json(x: 'All'):
    if (not isinstance(x,All)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(All)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["children"] = list(map(Intent.to_json, x.children))
    return d


class Any(Intent):
  def __init__(self, threshold: uint64, children: list[Intent]):
    super().__init__()
    self.threshold = threshold
    self.children = children

  @staticmethod
  def from_json(d):
    return Any(d["threshold"], list(map(Intent.from_json, d["children"])))

  @staticmethod
  def to_json(x: 'Any'):
    if (not isinstance(x,Any)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Any)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["threshold"] = x.threshold
    d["children"] = list(map(Intent.to_json, x.children))
    return d


class Restriction(Intent):
  def __init__(self, lhs: Expr, relation: Relation, rhs: Expr):
    super().__init__()
    self.lhs = lhs
    self.relation = relation
    self.rhs = rhs

  @staticmethod
  def from_json(d):
    return Restriction(Expr.from_json(d["lhs"]), Relation.from_json(d["relation"]), Expr.from_json(d["rhs"]))

  @staticmethod
  def to_json(x: 'Restriction'):
    if (not isinstance(x,Restriction)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Restriction)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["lhs"] = Expr.to_json(x.lhs)
    d["relation"] = Relation.to_json(x.relation)
    d["rhs"] = Expr.to_json(x.rhs)
    return d


class Finite(Intent):
  def __init__(self, uses: uint64, inner: Intent):
    super().__init__()
    self.uses = uses
    self.inner = inner

  @staticmethod
  def from_json(d):
    return Finite(d["uses"], Intent.from_json(d["inner"]))

  @staticmethod
  def to_json(x: 'Finite'):
    if (not isinstance(x,Finite)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Finite)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["uses"] = x.uses
    d["inner"] = Intent.to_json(x.inner)
    return d


class Temporary(Intent):
  def __init__(self, duration: int, availableAfter: bool, inner: Intent):
    super().__init__()
    self.duration = duration
    self.availableAfter = availableAfter
    self.inner = inner

  @staticmethod
  def from_json(d):
    return Temporary(d["duration"], d["availableAfter"], Intent.from_json(d["inner"]))

  @staticmethod
  def to_json(x: 'Temporary'):
    if (not isinstance(x,Temporary)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Temporary)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["duration"] = x.duration
    d["availableAfter"] = x.availableAfter
    d["inner"] = Intent.to_json(x.inner)
    return d


class Signature(Intent):
  def __init__(self, signer: G2Element):
    super().__init__()
    self.signer = signer

  @staticmethod
  def from_json(d):
    return Signature(d["signer"])

  @staticmethod
  def to_json(x: 'Signature'):
    if (not isinstance(x,Signature)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Signature)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["signer"] = x.signer
    return d


# BridgeInstruction types

class BridgeInstruction():
  def __init__(self):
    pass

  @staticmethod
  def from_json(d):
    match d["tag"]:
      case "Burn":
        return Burn.from_json(d)
      case "Mint":
        return Mint.from_json(d)

  @staticmethod
  def to_json(x: 'BridgeInstruction'):
    if (not isinstance(x,BridgeInstruction)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(BridgeInstruction)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    match x:
      case Burn():
        d = {"tag" : "Burn"} | Burn.to_json(x)
        return dict(sorted(d.items()))
      case Mint():
        d = {"tag" : "Mint"} | Mint.to_json(x)
        return dict(sorted(d.items()))


class Burn(BridgeInstruction):
  def __init__(self, token: Token, amount: float64):
    super().__init__()
    self.token = token
    self.amount = amount

  @staticmethod
  def from_json(d):
    return Burn(Token.from_json(d["token"]), d["amount"])

  @staticmethod
  def to_json(x: 'Burn'):
    if (not isinstance(x,Burn)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Burn)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["token"] = Token.to_json(x.token)
    d["amount"] = x.amount
    return d


class Mint(BridgeInstruction):
  def __init__(self, prover: G2Element, token: Token, amount: float64):
    super().__init__()
    self.prover = prover
    self.token = token
    self.amount = amount

  @staticmethod
  def from_json(d):
    return Mint(d["prover"], Token.from_json(d["token"]), d["amount"])

  @staticmethod
  def to_json(x: 'Mint'):
    if (not isinstance(x,Mint)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Mint)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["prover"] = x.prover
    d["token"] = Token.to_json(x.token)
    d["amount"] = x.amount
    return d


# Instruction types

class Instruction():
  def __init__(self):
    pass

  @staticmethod
  def from_json(d):
    match d["tag"]:
      case "TransferFunds":
        return TransferFunds.from_json(d)
      case "OrIntent":
        return OrIntent.from_json(d)
      case "SetIntent":
        return SetIntent.from_json(d)
      case "Delete":
        return Delete.from_json(d)
      case "Bridge":
        return Bridge.from_json(d)

  @staticmethod
  def to_json(x: 'Instruction'):
    if (not isinstance(x,Instruction)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Instruction)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    match x:
      case TransferFunds():
        d = {"tag" : "TransferFunds"} | TransferFunds.to_json(x)
        return dict(sorted(d.items()))
      case OrIntent():
        d = {"tag" : "OrIntent"} | OrIntent.to_json(x)
        return dict(sorted(d.items()))
      case SetIntent():
        d = {"tag" : "SetIntent"} | SetIntent.to_json(x)
        return dict(sorted(d.items()))
      case Delete():
        d = {"tag" : "Delete"} | Delete.to_json(x)
        return dict(sorted(d.items()))
      case Bridge():
        d = {"tag" : "Bridge"} | Bridge.to_json(x)
        return dict(sorted(d.items()))


class TransferFunds(Instruction):
  def __init__(self, source: G2Element, target: G2Element, funds: dict[Token,float64]):
    super().__init__()
    self.source = source
    self.target = target
    self.funds = funds

  @staticmethod
  def from_json(d):
    return TransferFunds(d["source"], d["target"], dict(d["funds"]))

  @staticmethod
  def to_json(x: 'TransferFunds'):
    if (not isinstance(x,TransferFunds)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(TransferFunds)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["source"] = x.source
    d["target"] = x.target
    d["funds"] = list(x.funds.items())
    return d


class OrIntent(Instruction):
  def __init__(self, host: G2Element, intent: Intent):
    super().__init__()
    self.host = host
    self.intent = intent

  @staticmethod
  def from_json(d):
    return OrIntent(d["host"], Intent.from_json(d["intent"]))

  @staticmethod
  def to_json(x: 'OrIntent'):
    if (not isinstance(x,OrIntent)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(OrIntent)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["host"] = x.host
    d["intent"] = Intent.to_json(x.intent)
    return d


class SetIntent(Instruction):
  def __init__(self, host: G2Element, intent: Intent):
    super().__init__()
    self.host = host
    self.intent = intent

  @staticmethod
  def from_json(d):
    return SetIntent(d["host"], Intent.from_json(d["intent"]))

  @staticmethod
  def to_json(x: 'SetIntent'):
    if (not isinstance(x,SetIntent)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(SetIntent)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["host"] = x.host
    d["intent"] = Intent.to_json(x.intent)
    return d


class Delete(Instruction):
  def __init__(self, host: G2Element):
    super().__init__()
    self.host = host

  @staticmethod
  def from_json(d):
    return Delete(d["host"])

  @staticmethod
  def to_json(x: 'Delete'):
    if (not isinstance(x,Delete)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Delete)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["host"] = x.host
    return d


class Bridge(Instruction):
  def __init__(self, bridgedAccount: G2Element, instruction: BridgeInstruction):
    super().__init__()
    self.bridgedAccount = bridgedAccount
    self.instruction = instruction

  @staticmethod
  def from_json(d):
    return Bridge(d["bridgedAccount"], BridgeInstruction.from_json(d["instruction"]))

  @staticmethod
  def to_json(x: 'Bridge'):
    if (not isinstance(x,Bridge)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Bridge)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["bridgedAccount"] = x.bridgedAccount
    d["instruction"] = BridgeInstruction.to_json(x.instruction)
    return d


class Transaction():
  def __init__(self, instructions: NonEmpty[Instruction]):
    super().__init__()
    self.instructions = instructions

  @staticmethod
  def from_json(d):
    return Transaction(NonEmpty.from_list(list(map(Instruction.from_json, (d["instructions"])))))

  @staticmethod
  def to_json(x: 'Transaction'):
    if (not isinstance(x,Transaction)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Transaction)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["instructions"] = list(map(Instruction.to_json, x.instructions.list))
    return d


class Signed():
  def __init__(self, nonce: UUID, signature: G1Element, signee: Transaction, signers: NonEmpty[G2Element]):
    super().__init__()
    self.nonce = nonce
    self.signature = signature
    self.signee = signee
    self.signers = signers

  @staticmethod
  def from_json(d):
    return Signed(d["nonce"], d["signature"], Transaction.from_json(d["signee"]), NonEmpty.from_list((d["signers"])))

  @staticmethod
  def to_json(x: 'Signed'):
    if (not isinstance(x,Signed)):
      raise TypeError (''+ '\n' + '  ' + 'Expected: ' + str(Signed)+ '\n' + '  ' + 'Got: ' + str(type(x)))
    d = dict()
    d["nonce"] = x.nonce
    d["signature"] = x.signature
    d["signee"] = Transaction.to_json(x.signee)
    d["signers"] = x.signers.list
    return d

