def PorscheEngine(self):
    pass


def BenzEngine(self):
    pass


def getCar(engine):
    class Car:
        engine = engine

        def start(self):
            self.engine()

    return Car


Benz = getCar(BenzEngine)
Porsche = getCar(PorscheEngine)
benz = Benz()
benz.start()
