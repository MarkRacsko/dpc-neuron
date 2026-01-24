FLAGS = "--enable-plugins=tk-inter"

build:
	@uv run nuitka --standalone main.py $(FLAGS)

clean:
	@rm -rf main.build
	@rm -rf main.dist