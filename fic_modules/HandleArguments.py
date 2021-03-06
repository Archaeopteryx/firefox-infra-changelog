class HandleArgs(object):
    def input_argument(self, argument):
        method_name = "method_" + str(argument).replace("-", "")
        print("Method name is: ", method_name)
        method = getattr(self, method_name, lambda: "Invalid argument!")
        return method()

    def method_default(self):
        print("No argument available!")
        return None

    def method_git(self):
        print("Runs in git only!")
        return ""

    def method_hg(self):
        print("Runs in HG only!")
        return ""

    def method_r(self):
        print("Runs in L only!")
        return ""


