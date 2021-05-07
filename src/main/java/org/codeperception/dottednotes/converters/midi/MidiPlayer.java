package org.codeperception.dottednotes.converters.midi;

import java.io.File;
import java.util.*;
import javax.sound.midi.*;

public class MidiPlayer {

  static final int SLEEP_TIME = 1000;
  private Synthesizer synthesizer;
  private Sequencer sequencer;

  public MidiPlayer() throws MidiUnavailableException, InvalidMidiDataException {
    sequencer = MidiSystem.getSequencer();
    synthesizer = MidiSystem.getSynthesizer();
    sequencer.open();
    synthesizer.open();
    sequencer.getTransmitter().setReceiver(synthesizer.getReceiver());
    //sequencer.setTempoInBPM(100);
  }

  /** Load a Soundfont (extension .sf2 or .dls) for use with the Synthesizer.
   * @return true if the Soundfont was loaded successfully, false otherwise.
   */
  public boolean loadSoundbank(File file) {
    try {
      Soundbank soundbank = MidiSystem.getSoundbank(file);
      if (synthesizer.isSoundbankSupported(soundbank)) {
        return synthesizer.loadAllInstruments(soundbank);
      }
    } catch (javax.sound.midi.InvalidMidiDataException e) {
      return false;
    } catch (java.io.IOException e) {
      return false;
    }
    return false;
  }

  public void setSequence(Sequence sequence) throws InvalidMidiDataException {
    sequencer.setSequence(sequence);
  }

  public void start() {
    sequencer.start();
  }

  public boolean isRunning() {
    return sequencer.isRunning();
  }

  public void stop() {
    sequencer.stop();
  }

  public void close() {
    if (isRunning()) {
      stop();
    }
    sequencer.close();
    synthesizer.close();
  }

  public void play(Sequence sequence) {
    try {
      setSequence(sequence);
      if (sequence != null) {}
      start();
      while (true) {
        try {
          Thread.sleep(SLEEP_TIME);
        } catch (InterruptedException e) {
          stop();
          close();
        }
        if (!isRunning()) {
          close();
          break;
        }
      }
    } catch (InvalidMidiDataException e) {
      e.printStackTrace();
    }
  }
}
