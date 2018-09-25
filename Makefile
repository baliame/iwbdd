all: build/build build/install backgrounds.bgs spritesheets.sss tilesets.tls

build: build/build

install: build/install

build/build:
	mkdir -p build
	touch build/build

build/install: build/install iwbdd/*.py iwbdd/pygame_oo/*.py
	python setup.py install
	touch build/install

backgrounds.bgs: build/install bg_*.png
	iwbdd_bgp backgrounds.bgs bg_clouds.png

spritesheets.sss: build/install ss_*.png
	iwbdd_ssp spritesheets.sss ss_player_spritesheet-16-16.png ss_player_doublejump_attachments-16-16.png ss_object_movingplatform-32-32.png

tilesets.tls: build/install ts_*.png
	iwbdd_tlp tilesets.tls ts_grass.png

.PHONY: all build install