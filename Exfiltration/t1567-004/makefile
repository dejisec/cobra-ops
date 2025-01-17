WINDOWS_TARGET = x86_64-pc-windows-gnu

CARGO = cargo
BUILD_DIR = target
OUTPUT_DIR = ./build

# Default target is native compilation
.PHONY: all
all: build

# Build for the host system
.PHONY: build
build:
	$(CARGO) build --release --target-dir=$(OUTPUT_DIR)
	@mv $(OUTPUT_DIR)/release/$(shell basename $(shell pwd)) ./

# Cross-compile for Windows
.PHONY: windows
windows:
	$(CARGO) build --release --target=$(WINDOWS_TARGET) --target-dir=$(OUTPUT_DIR)
	@mv $(OUTPUT_DIR)/$(WINDOWS_TARGET)/release/$(shell basename $(shell pwd)).exe ./

# Clean the build artifacts
.PHONY: clean
clean:
	$(CARGO) clean
	@rm -rf ./build
	@rm -f $(shell basename $(shell pwd))*