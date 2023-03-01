# bababooey
Discord Sound Effect Bot


## TODO
- [ ] add new sound effects
  - [ ] Cancel button (with file cleanup and message deletion)
- [ ] History includes the date, formats to ET


## Near-term
- [ ] Waveform is mono
- [ ] Waveform has time lines
- [ ] Waveform has overview and zoomed-in
- [ ] Auto re-draw the soundboard once a new sound is added
- [ ] import the sound effect history from old logs
- [ ] logging for commands


## Bugs
- [ ] When you request while not in a voice channel, it should join whatever has people.
- [ ] We need a lock when redrawing the sound board.
- [ ] Sometimes the tags/times are empty in the modal even though you just edited it.
- [ ] Downloading https://www.youtube.com/watch?v=Sk8QzckJvUI cuts it off at the end (youtubedl returns whole integer seconds, we need millis)

## Distant features
- [ ] Monkeytime
- [ ] Check the length before doing download.
- [ ] sound effect pallets
- [ ] sound effect combos chain multiple sound effects together 
- [ ] command to generate sound effect usage graphs
- [ ] History refreshes (maybe at the bottom of the soundboar channel)
  
## Resources
- [ ] Waveform image (https://stackoverflow.com/questions/32254818/generating-a-waveform-using-ffmpeg)