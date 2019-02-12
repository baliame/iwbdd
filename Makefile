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
	iwbdd_ssp spritesheets.sss ss_player_spritesheet-24-24.png ss_player_doublejump_attachments-24-24.png ss_object_movingplatform-32-32.png ss_object_small_pickups-8-8.png ss_object_bullets-8-8.png ss_object_shootables-24-24.png ss_object_ttsboss_objects-24-72.png ss_boss_tts-120-120.png ss_boss_tts_bullets-24-24.png ss_boss_tts_ats-48-48.png ss_explosion-48-48.png ss_boss_barrier-24-144.png

tilesets.tls: ts_*.png | build/install
	iwbdd_tsp tilesets.tls ts_grass.png ts_anor_londo.png ts_collision.png

audio.dat: *.ogg | build/install
	iwbdd_adp audio.dat *.ogg

.PHONY: all build install