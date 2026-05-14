from jurigged.notebook import patch_namespace


def test_patch_namespace_function_identity_and_behavior():
    ns = {"__name__": "__main__"}
    exec("def f(x):\n    return x + 1\n", ns, ns)
    f_before = ns["f"]

    before = {"f": f_before}
    exec("def f(x):\n    return x + 2\n", ns, ns)
    f_after = ns["f"]
    assert f_after is not f_before

    patch_namespace(before, ns, module_name="__main__")
    assert ns["f"] is f_before
    assert f_before(1) == 3


def test_patch_namespace_class_updates_existing_instances():
    ns = {"__name__": "__main__"}
    exec(
        "class A:\n"
        "    def m(self):\n"
        "        return 1\n",
        ns,
        ns,
    )
    A_before = ns["A"]
    inst = A_before()

    before = {"A": A_before}
    exec(
        "class A:\n"
        "    def m(self):\n"
        "        return 2\n",
        ns,
        ns,
    )

    patch_namespace(before, ns, module_name="__main__")
    assert ns["A"] is A_before
    assert inst.m() == 2


def test_patch_namespace_class_methods_are_patched_in_place():
    ns = {"__name__": "__main__"}
    exec(
        "class A:\n"
        "    @staticmethod\n"
        "    def s(x):\n"
        "        return x + 1\n"
        "    @classmethod\n"
        "    def c(cls, x):\n"
        "        return x + 1\n",
        ns,
        ns,
    )
    A_before = ns["A"]
    s_before = A_before.__dict__["s"].__func__
    c_before = A_before.__dict__["c"].__func__

    before = {"A": A_before}
    exec(
        "class A:\n"
        "    @staticmethod\n"
        "    def s(x):\n"
        "        return x + 2\n"
        "    @classmethod\n"
        "    def c(cls, x):\n"
        "        return x + 2\n",
        ns,
        ns,
    )

    patch_namespace(before, ns, module_name="__main__")

    assert ns["A"] is A_before
    assert A_before.s(1) == 3
    assert A_before.c(1) == 3
    assert A_before.__dict__["s"].__func__ is s_before
    assert A_before.__dict__["c"].__func__ is c_before

