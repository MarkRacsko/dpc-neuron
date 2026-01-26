FLAGS = "--enable-plugins=tk-inter"

build:
	@uv run nuitka --standalone main.py $(FLAGS)

clean:
	@rm -rf main.build
	@rm -rf main.dist

smooth:
	@uv run src/neuron/compiled/compile_smooth.py build_ext --inplace
	@mv src/neuron/compiled/cy_smooth.cpython*.so src/neuron/compiled/cy_smooth.so