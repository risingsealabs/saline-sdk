# Auto-generated - do not edit manually

import json
import unittest
from saline_sdk.transaction.bindings import *

def roundtrip(from_json, to_json, values):
  for serialized in values:
    parsed = from_json(loads(serialized))
    reserialized = dumps(to_json(parsed))
    if serialized != reserialized:
      print('Failed to roundtrip')
      print('Expected: ' + serialized)
      print('Got: ' + reserialized)
      exit(1)


class TestRoundtrips(unittest.TestCase):
  def test_roundtrips(self):
    roundtrip((lambda x: x), (lambda x: x), ['false', 'true'])

    roundtrip((lambda x: x), (lambda x: x), ['4336857'])

    roundtrip((lambda x: x), (lambda x: x), ['21847545125112684826220722557248124029534906783074'])

    roundtrip((lambda x: x), (lambda x: x), ['"a8265f375fcf1655aa810f1aa319ea15360798d8006d071de0cbfa925d593bbbd2162379134bed76df61a251d202c42c"'])

    roundtrip((lambda x: Relation.from_json(x)), (lambda x: Relation.to_json(x)), ['"EQ"', '"LT"', '"LE"', '"GT"', '"GE"'])

    roundtrip((lambda x: Token.from_json(x)), (lambda x: Token.to_json(x)), ['"BTC"', '"ETH"', '"USDC"', '"USDT"', '"SALT"'])

    roundtrip((lambda x: Arithmetic.from_json(x)), (lambda x: Arithmetic.to_json(x)), ['"Add"', '"Div"', '"Mul"', '"Sub"'])

    roundtrip((lambda x: VariableTag.from_json(x)), (lambda x: VariableTag.to_json(x)), ['"Address"', '"Amount"', '"Count"', '"List"'])

    roundtrip((lambda x: Variable.from_json(x)), (lambda x: Variable.to_json(x)), ['{"kind":"Address","name":"Foo"}'])

    roundtrip((lambda x: Expr.from_json(x)), (lambda x: Expr.to_json(x)), ['{"lhs":{"tag":"Lit","value":85053},"operation":"Sub","rhs":{"lhs":{"tag":"Send","token":"USDC"},"operation":"Mul","rhs":{"lhs":{"tag":"Lit","value":18207},"operation":"Div","rhs":{"tag":"Var","var":{"kind":"Amount","name":"Baz"}},"tag":"Arithmetic2"},"tag":"Arithmetic2"},"tag":"Arithmetic2"}'])

    roundtrip((lambda x: Expr.from_json(x)), (lambda x: Expr.to_json(x)), ['{"tag":"Var","var":{"kind":"Address","name":"Baz"}}'])

    roundtrip((lambda x: Intent.from_json(x)), (lambda x: Intent.to_json(x)), ['{"availableAfter":true,"duration":-15.344827586207,"inner":{"availableAfter":false,"duration":-6.1875,"inner":{"availableAfter":true,"duration":-16.5,"inner":{"inner":{"inner":{"address":"81a1f8200061a1dc03b6c6bdf0dbcbcd7fd9077e05e118722710e920987d5f4c90b6958a521c253c667713b8c46ff02f","tag":"Counterparty"},"tag":"Finite","uses":7653953},"tag":"Finite","uses":13144222},"tag":"Temporary"},"tag":"Temporary"},"tag":"Temporary"}'])

    roundtrip((lambda x: Witness.from_json(x)), (lambda x: Witness.to_json(x)), ['{"children":[],"tag":"AllW"}'])

    roundtrip((lambda x: Transaction.from_json(x)), (lambda x: Transaction.to_json(x)), ['{"burn":[["8476157a1a10ec32574b66cc315402ad0eb52f92376a4571a51e369bcbf4774a5579fafbed4ec3feb4b7918fa8ab675b",[["USDT",441945]]],["97a79ff2de9f668c139ba635ad4ffe06edf39ed61d81a75dcf63096068bc9f94873a1c8f2e0e8d581372961debc6b047",[["BTC",470334],["USDC",691787]]],["b0b5d026c666b15badf959dd57322fb3ec5e33f3281fb4246eb593e786318d3c3e1d1e1cecc3daa79cf16a8a0cfc988f",[["BTC",274991],["ETH",84752],["USDT",593122],["SALT",933205]]]],"funds":[["8017777cffcc94fd9ad4af36124ff380716de766c3115d2444f83a63f0563cbbd53797c83704c815f3cae25fc388c946",[["882085f6ea23884140e9b15bb9706afd44c67df4682376885b83ca80f8a70ed496683ad04499261f7c60d01003c6d152",[["ETH",327225],["USDC",933026]]]]],["80e945b0ef5caa977e39cd88642f40d6a6c8960e976444288041eef0989341458ccad0249d29e35236236780d1cc8a3e",[["b583ac73247cb0e845f3958ba52bc365dbe5eb175ca5df10400ffe97ed784d158c63f79b96bfcb21edb039723c95e65d",[["USDT",840451]]]]],["a240774feb2618db84428bbeec37f4e3d888a0667b29a8ba45abda9a364143dcd83138084bbba8ae3396ad06ce477c5a",[["b4bd50f973975afc1cdeda5d4b85cebbf55257e444046b12428773cf3a143f158a2d6fdc2685717e189c1bda97bdec4f",[["BTC",54365]]]]],["b583ac73247cb0e845f3958ba52bc365dbe5eb175ca5df10400ffe97ed784d158c63f79b96bfcb21edb039723c95e65d",[["92b2b92cb0fa07cff421896157b510d12626aff38bf7bd71c55715110577fb6b9c265f5d05787a52251307e5d6f9b903",[["BTC",616858]]]]]],"intents":[["8578180ac3422e4e531eeec40513343693d139c9bd7fc03c7436f2ec8057b3d195de84726f868c560f364f395ccb821a",{"intent":{"address":"92b2b92cb0fa07cff421896157b510d12626aff38bf7bd71c55715110577fb6b9c265f5d05787a52251307e5d6f9b903","tag":"Counterparty"},"tag":"OrIntent"}],["92b2b92cb0fa07cff421896157b510d12626aff38bf7bd71c55715110577fb6b9c265f5d05787a52251307e5d6f9b903",{"intent":{"children":[{"inner":{"children":[{"inner":{"children":[],"tag":"Any","threshold":8575966},"tag":"Finite","uses":4017640}],"tag":"Any","threshold":8977933},"tag":"Finite","uses":3084983}],"tag":"Any","threshold":12447931},"tag":"OrIntent"}],["979c28967ab41ddc6c05714532c2faa38e9fc0a58f0b683089c5364d2805e5714c182541049a3b95538c089d3d9afd01",{"intent":{"lhs":{"tag":"Send","token":"USDC"},"relation":"LE","rhs":{"lhs":{"tag":"Balance","token":"BTC"},"operation":"Sub","rhs":{"tag":"Balance","token":"BTC"},"tag":"Arithmetic2"},"tag":"Restriction"},"tag":"OrIntent"}],["98cfbea7db13af8b0aafec4795ff2d6873b737acf681bd503dcdc95f4f8486b7ba77926a47e2a4e3dd2944fd3b86509f",{"intent":{"signer":"8144a5f375d27612bcb874f262c2db443c8a898baaf74a1fa3458743ba2f221f5df0cf7b8f298a6249e13a0aecb23cac","tag":"Signature"},"tag":"SetIntent"}]],"mint":[]}'])

    roundtrip((lambda x: Signed.from_json(x)), (lambda x: Signed.to_json(x)), ['{"nonce":"843af8fa-8ab0-b451-5b90-381abc36a640","signature":"95c5611331ab6e8326f38231e2959c2e52facadf3e61a29f67c3e92fae129d9382f4e59042c304b1ff8105b0dfe3543207d1190b62280309eb28bfddd51a2c2b00adc5fe0f01bbb0224800d40df6ebfe876e1db34a29e746d46502639a40b029","signee":{"burn":[["8144a5f375d27612bcb874f262c2db443c8a898baaf74a1fa3458743ba2f221f5df0cf7b8f298a6249e13a0aecb23cac",[]],["8a12b4da2321ac71ac25dca3e0d06cc23e464d5e1edf684954ee7214a08b30264e2250db1314bcaedb10b1294cb0266b",[["BTC",549248],["USDT",748980],["SALT",787515]]],["b14e416f1b211a1d08066c8c7e092d7c056e39909fd4c6c383d3cd3ea8f5eac6ab8f3bb43917e69ceef185f7c96d0ef5",[["USDT",818390],["SALT",513960]]]],"funds":[["91f4d2f31c03d9e14721f480b0a432da3509db110929ad9ed79617d53eb4f2aa0704994505f114c569e554e562631d92",[["979c28967ab41ddc6c05714532c2faa38e9fc0a58f0b683089c5364d2805e5714c182541049a3b95538c089d3d9afd01",[["BTC",90147],["SALT",464469]]]]]],"intents":[["8144a5f375d27612bcb874f262c2db443c8a898baaf74a1fa3458743ba2f221f5df0cf7b8f298a6249e13a0aecb23cac",{"intent":{"children":[{"lhs":{"tag":"Var","var":{"kind":"Amount","name":"Foo"}},"relation":"GE","rhs":{"tag":"Send","token":"USDC"},"tag":"Restriction"}],"tag":"Any","threshold":2191158},"tag":"SetIntent"}],["a812924daf22c266255d43e764578633ad4f8de0be6226f5236855fbdc73b85b078abc26d4787a955214e8d36a5be38a",{"intent":{"lhs":{"tag":"Receive","token":"BTC"},"relation":"LT","rhs":{"tag":"Var","var":{"kind":"Amount","name":"Baz"}},"tag":"Restriction"},"tag":"SetIntent"}]],"mint":[]},"signers":["aa3b953ef528f2dc743e4b9eda7eccadce0f25ade20c93d57644897bb4ef3a80299f06695124504e0a2eead54f75d9a3"]}'])

