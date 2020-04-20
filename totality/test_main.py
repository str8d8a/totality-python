from totality import Totality, Node, NodeId

def test_basic():
    t = Totality()
    coll = t.create_collection(username="system")
    node_id = NodeId(node_type="facility")
    node = Node(node_id, 34, -120, collection=coll)
    print(node.to_doc())
    assert t is not None