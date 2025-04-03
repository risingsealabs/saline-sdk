import unittest

from saline_sdk.crypto import derive_master_SK, derive_child_SK

class EIP2333TestCase(unittest.TestCase):
    def test_case_0(self):
        # Test Case 0
        seed_hex = (
            "c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e5349553"
            "1f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04"
        )
        seed = bytes.fromhex(seed_hex)
        master_sk = derive_master_SK(seed)
        expected_master_sk_int = 6083874454709270928345386274498605044986640685124978867557563392430687146096
        obtained_master_sk_int = int.from_bytes(bytes(master_sk), "big")
        self.assertEqual(
            obtained_master_sk_int, expected_master_sk_int,
            "Test case 0: Master key mismatch"
        )

        child_index = 0
        child_sk = derive_child_SK(master_sk, child_index)
        expected_child_sk_int = 20397789859736650942317412262472558107875392172444076792671091975210932703118
        obtained_child_sk_int = int.from_bytes(bytes(child_sk), "big")
        self.assertEqual(
            obtained_child_sk_int, expected_child_sk_int,
            "Test case 0: Child key mismatch"
        )

    def test_case_1(self):
        # Test Case 1
        seed_hex = "3141592653589793238462643383279502884197169399375105820974944592"
        seed = bytes.fromhex(seed_hex)
        master_sk = derive_master_SK(seed)
        expected_master_sk_int = 29757020647961307431480504535336562678282505419141012933316116377660817309383
        obtained_master_sk_int = int.from_bytes(bytes(master_sk), "big")
        self.assertEqual(
            obtained_master_sk_int, expected_master_sk_int,
            "Test case 1: Master key mismatch"
        )

        child_index = 3141592653
        child_sk = derive_child_SK(master_sk, child_index)
        expected_child_sk_int = 25457201688850691947727629385191704516744796114925897962676248250929345014287
        obtained_child_sk_int = int.from_bytes(bytes(child_sk), "big")
        self.assertEqual(
            obtained_child_sk_int, expected_child_sk_int,
            "Test case 1: Child key mismatch"
        )

    def test_case_2(self):
        # Test Case 2
        seed_hex = "0099FF991111002299DD7744EE3355BBDD8844115566CC55663355668888CC00"
        seed = bytes.fromhex(seed_hex)
        master_sk = derive_master_SK(seed)
        expected_master_sk_int = 27580842291869792442942448775674722299803720648445448686099262467207037398656
        obtained_master_sk_int = int.from_bytes(bytes(master_sk), "big")
        self.assertEqual(
            obtained_master_sk_int, expected_master_sk_int,
            "Test case 2: Master key mismatch"
        )

        child_index = 4294967295
        child_sk = derive_child_SK(master_sk, child_index)
        expected_child_sk_int = 29358610794459428860402234341874281240803786294062035874021252734817515685787
        obtained_child_sk_int = int.from_bytes(bytes(child_sk), "big")
        self.assertEqual(
            obtained_child_sk_int, expected_child_sk_int,
            "Test case 2: Child key mismatch"
        )

    def test_case_3(self):
        # Test Case 3
        seed_hex = "d4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
        seed = bytes.fromhex(seed_hex)
        master_sk = derive_master_SK(seed)
        expected_master_sk_int = 19022158461524446591288038168518313374041767046816487870552872741050760015818
        obtained_master_sk_int = int.from_bytes(bytes(master_sk), "big")
        self.assertEqual(
            obtained_master_sk_int, expected_master_sk_int,
            "Test case 3: Master key mismatch"
        )

        child_index = 42
        child_sk = derive_child_SK(master_sk, child_index)
        expected_child_sk_int = 31372231650479070279774297061823572166496564838472787488249775572789064611981
        obtained_child_sk_int = int.from_bytes(bytes(child_sk), "big")
        self.assertEqual(
            obtained_child_sk_int, expected_child_sk_int,
            "Test case 3: Child key mismatch"
        )

if __name__ == '__main__':
    unittest.main()
