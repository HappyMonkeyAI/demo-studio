# Demo pack: mrpg-realms

Public product: [MRPG Realms](https://realms.happymonkey.ai/) — multiplayer voxel realm (Happy Monkey).

Story and facts are taken from the player wiki at [`/wiki/`](https://realms.happymonkey.ai/wiki/) (getting started, structures, settlement, combat, Realm War preview).

```bash
export DEMO_BASE_URL=https://realms.happymonkey.ai
demo-studio validate demos/mrpg-realms/demo.beats.json
demo-studio capture demos/mrpg-realms/demo.beats.json --run-dir outputs/realms-run --engine playwright
demo-studio narrate demos/mrpg-realms/demo.beats.json outputs/realms-run --provider piper
demo-studio package outputs/realms-run --title-card "MRPG Realms" --subtitle "voxel multiplayer · wiki"
```

Beats stay on the join screen + wiki (readable, stable for capture). Entering the WebGL realm mid-demo is optional follow-up — canvas stills need a loaded session and are less repeatable than wiki pages.
