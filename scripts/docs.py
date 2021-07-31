from ruqqus.__main__ import app

class Doc():

    def __init(self, **kwargs):
        for entry in kwargs:
            self.__dict__[entry]=kwargs[entry]

    def __str__(self):

        return f"{self.method.upper()} {self.endpoint}\n\n{self.docstring}"

    @property
    def docstring(self):
        return self.target_function.__doc__

docs=[]

for rule in app.url_map.iter_rules():

    if not rule.rule.startswith("/api/v2/"):
        continue

    endpoint=rule.split("api/v2")[1]

    for method in rule.methods:
        if method not in ["OPTIONS","HEAD"]:
            break


    new_doc=Doc(
        method=method,
        endpoint=endpoint,
        target_function = eval(rule.endpoint)
        )

