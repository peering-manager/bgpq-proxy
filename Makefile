PROJECT=bgpqproxy
BLACK=black
ISORT=isort

all: run

lint:
	$(BLACK) $(PROJECT) && $(ISORT) $(PROJECT)

run:
	env FLASK_ENV=development FLASK_APP=$(PROJECT) flask run

.PHONY: all lint run
