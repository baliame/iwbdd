all: build/build build/install backgrounds.bgs spritesheets.sss tilesets.tls

build: build/build

install: build/build build/install

build/build:
	mkdir build
	touch build/build

build/install: build/build setup.py iwbdd/*.py iwbdd/pygame_oo/*.py
	python setup.py install
	touch build/install

backgrounds.bgs: bg_*.png | build/install
	iwbdd_bgp backgrounds.bgs bg_clouds.png

spritesheets.sss: ss_*.png | build/install
	iwbdd_ssp spritesheets.sss ss_player_spritesheet-24-24.png ss_player_doublejump_attachments-24-24.png ss_object_movingplatform-32-32.png

tilesets.tls: ts_*.png | build/install
	iwbdd_tsp tilesets.tls ts_grass.png

.PHONY: all build install