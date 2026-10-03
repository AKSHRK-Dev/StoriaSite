---
summary: Store the world in the Linear region format and use about half the disk space. Existing worlds are converted as they are used.
---
!!! note "Beta"
    The Linear region format is part of Storia **26.2-9-beta** and later. Back up your world before switching.

The **Linear region format** stores each region (32 × 32 chunks) as one Zstandard stream in a single `r.X.Z.linear`
file ([format and tools](https://github.com/xymb-endcrystalme/LinearRegionFileFormatTools)). Vanilla's Anvil format
(`.mca`) compresses each chunk on its own with the old zlib and pads it to 4 KB, which wastes a lot of space.

| | Anvil (`.mca`) | Linear (`.linear`) |
| --- | --- | --- |
| Compression | zlib, per chunk | Zstandard, per region |
| Disk space (measured on Storia) | 100% | level 1: 55%, level 6: 46% |
| Reading or writing one chunk | quick | the whole region is kept in memory |
| Works with other tools | almost all | tools that know Linear |

Measured on 12 overworld regions (46.1 MB). The smaller the chunks (the End, for example), the bigger the difference.

## Using it

Switch it in `storia.yml` and restart the server:

```yaml
region-format:
  type: linear             # anvil (default) or linear
  linear:
    compression-level: 1   # 1 (fast) to 22 (small); around 6 shrinks a lot more
    flush-seconds: 5       # how often changed regions are written to disk
```

- **Existing worlds just work.** A region without a `.linear` file is read from its `.mca` the first time it is used
  and written as `.linear` from then on. The `.mca` files are left in place; delete them once you are happy, to free
  the space.
- To convert everything at once, stop the server and run `convert_region_files.py mca2linear` from the
  [Linear tools](https://github.com/xymb-endcrystalme/LinearRegionFileFormatTools). Storia reads the files they write,
  and they read the files Storia writes.
- Works with the [[ram-world]]: smaller files also need less RAM.
- `/storia status` shows how many regions are in memory and how many are waiting to be written.

## Good to know

- **Writes are batched.** Changed regions are written every `flush-seconds`, on `save-all flush` and on stop. If the
  server process dies suddenly, the last few seconds of chunk saves can be lost (with Anvil, the same is true for
  data the OS had not written yet).
- **Regions in use are kept in memory**: a few MB to a few tens of MB each. Regions unused for 60 seconds are dropped
  from memory.
- **An unreadable `.linear` file is never overwritten.** Its region is not loaded and not written, and the file is
  left as it is, so you can restore it from a backup.
- Tools and plugins that open `.mca` files themselves (some map renderers) cannot read `.linear`. Plugins that go
  through the server, such as Chunky, work as usual.
- Not used on [[cluster|Storia Cluster]] workers: Storia Relay stores the world in Anvil format.

## Going back to Anvil

Convert the `.linear` files back with the tools' `linear2mca` before setting `type: anvil`. If the world has
`.linear` files and `anvil` is selected, Storia **refuses to start**, so it never runs on the old `.mca` files and
seems to have lost recent changes.
