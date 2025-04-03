Transaction
===========

.. toctree::
   :maxdepth: 2
   :caption: Transaction Module:

   transaction/bindings

Transaction creation, signing, and submission.

.. automodule:: saline_sdk.transaction.tx
   :members:
   :undoc-members:
   :show-inheritance:

Instructions
-----------

.. automodule:: saline_sdk.transaction.instructions
   :members:
   :undoc-members:
   :show-inheritance:

Serialization
------------

.. automodule:: saline_sdk.transaction.serialisation
   :members:
   :undoc-members:
   :show-inheritance:

Transaction Class
----------------

.. automodule:: saline_sdk.transaction
   :members:
   :undoc-members:
   :show-inheritance: 

.. autoclass:: saline_sdk.transaction.sdk.Transaction
   :members:
   :undoc-members:
   :show-inheritance:
   
.. autoclass:: saline_sdk.transaction.sdk.Signed
   :members:
   :undoc-members:
   :show-inheritance:
   
Transaction Operations
---------------------

.. currentmodule:: saline_sdk.transaction.tx

.. autofunction:: prepareSimpleTx
.. autofunction:: encodeSignedTx
.. autofunction:: sign

Transaction Instructions
-----------------------

.. currentmodule:: saline_sdk.transaction.instructions

.. autofunction:: transfer
.. autofunction:: swap
.. autofunction:: set_intent

Transaction Serialization
------------------------

.. automodule:: saline_sdk.transaction.serialisation
   :members:
   :undoc-members:
   :show-inheritance: 