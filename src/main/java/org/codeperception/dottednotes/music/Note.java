/**
 * DottedNotes: -- Braille Music Conversion Utility
 *
 * Copyright 2021 Judith Lung  All Rights Reserved.
 *
 * This code is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License version 3, as
 * published by the Free Software Foundation.
 *
 * This code is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this work; if not, see <http://www.gnu.org/licenses/>.
 */

package org.codeperception.dottednotes.music;

import java.util.ArrayList;
import java.util.HashMap;
import org.codeperception.dottednotes.math.Fraction;

public class Note extends MeasureElement {

  int voiceNumber = 1;
  Pitch pitch;

  public Note(Measure measure, Pitch pitch, Fraction duration) {
    super(measure);
    this.pitch = pitch;
    this.duration = duration;
  }

  public Pitch getPitch() {
    return this.pitch;
  }

  String type;

  public String getType() {
    return this.type;
  }

  public void setType(String type) throws IllegalArgumentException {
    String[] availableTypes = new String[] {
      "1024th",
      "512th",
      "256th",
      "128th",
      "64th",
      "32nd",
      "16th",
      "eighth",
      "quarter",
      "half",
      "whole",
      "breve",
      "long",
      "maxima",
    };
    if (!Utils.contains(type, availableTypes)) {
      throw new IllegalArgumentException("Invalid note type: " + type);
    }
    this.type = type;
  }

  public Fraction getDurationFromType(String type) {
    HashMap<String, Fraction> typesToDurations = new HashMap<String, Fraction>();
    typesToDurations.put("1024th", new Fraction(1, 1024));
    typesToDurations.put("512th", new Fraction(1, 512));
    typesToDurations.put("256th", new Fraction(1, 256));
    typesToDurations.put("128th", new Fraction(1, 128));
    typesToDurations.put("64th", new Fraction(1, 64));
    typesToDurations.put("32nd", new Fraction(1, 32));
    typesToDurations.put("16th", new Fraction(1, 16));
    typesToDurations.put("eighth", new Fraction(1, 8));
    typesToDurations.put("quarter", new Fraction(1, 4));
    typesToDurations.put("half", new Fraction(1, 2));
    typesToDurations.put("whole", new Fraction(1, 1));
    typesToDurations.put("breve", new Fraction(2, 1));
    typesToDurations.put("long", new Fraction(4, 1));
    typesToDurations.put("maxima", new Fraction(0, 1));
    return typesToDurations.get(type);
  }

  public String getTypeFromDuration(Fraction duration) {
    HashMap<Fraction, String> durationsToTypes = new HashMap<Fraction, String>();
    durationsToTypes.put(new Fraction(1, 1024), "1024th");
    durationsToTypes.put(new Fraction(1, 512), "512th");
    durationsToTypes.put(new Fraction(1, 256), "256th");
    durationsToTypes.put(new Fraction(1, 128), "128th");
    durationsToTypes.put(new Fraction(1, 64), "64th");
    durationsToTypes.put(new Fraction(1, 32), "32nd");
    durationsToTypes.put(new Fraction(1, 16), "16th");
    durationsToTypes.put(new Fraction(1, 8), "eighth");
    durationsToTypes.put(new Fraction(1, 4), "quarter");
    durationsToTypes.put(new Fraction(1, 2), "half");
    durationsToTypes.put(new Fraction(1, 1), "whole");
    durationsToTypes.put(new Fraction(2, 1), "breve");
    durationsToTypes.put(new Fraction(4, 1), "long");
    durationsToTypes.put(new Fraction(0, 1), "maxima");
    return durationsToTypes.get(duration);
  }

  private boolean pizzicato = false;

  public boolean getPizzicato() {
    return this.pizzicato;
  }

  public void setPizzicato(boolean pizz) {
    this.pizzicato = pizz;
  }

  private Grace grace = null;

  public Grace getGrace() {
    return this.grace;
  }

  public void setGrace(Grace grace) {
    this.grace = grace;
  }

  private TimeModification timeModification;

  public TimeModification getTimeModification() {
    return this.timeModification;
  }

  public void setTimeModification(TimeModification timeModification) {
    this.timeModification = timeModification;
  }

  Tie tie;

  public Tie getTie() {
    return this.tie;
  }

  public void setTie(Tie tie) {
    this.tie = tie;
  }

  Slur slur;

  public Slur getSlur() {
    return this.slur;
  }

  public void setSlur(Slur slur) {
    this.slur = slur;
  }

  private String instrumentId;

  public String getInstrumentId() {
    return this.instrumentId;
  }

  public void setInstrumentId(String id) {
    this.instrumentId = id;
  }

  public Instrument getInstrument() {
    Instrument instrument = null;
    Part part = this.getMeasure().getPart();
    if (this.instrumentId != null) {
      String id = this.getInstrumentId();
      instrument = part.getInstrument(id);
    } else if (part.getInstruments().size() == 1) {
      instrument = part.getInstruments().get(0);
    }
    return instrument;
  }

  public int getMidiChannel() {
    if (this.getInstrument() != null) {
      return this.getInstrument().getMidiChannel();
    }
    return 0;
  }

  public int getMidiProgram() {
    if (this.getInstrument() != null) {
      return this.getInstrument().getMidiProgram();
    }
    return 0;
  }

  private boolean isDotted = false;

  public boolean getDotted() {
    return this.isDotted;
  }

  public void setDotted(boolean isDotted) {
    this.isDotted = isDotted;
  }

  private Accidental accidental = null;

  public Accidental getAccidental() {
    return this.accidental;
  }

  public void setAccidental(Accidental accidental) {
    this.accidental = accidental;
  }

  private Tuplet tuplet = null;

  public Tuplet getTuplet() {
    return this.tuplet;
  }

  public void setTuplet(Tuplet tuplet) {
    this.tuplet = tuplet;
  }

  private boolean hasGlissando = false;

  public boolean getGlissando() {
    return this.hasGlissando;
  }

  public void setGlissando(boolean hasGlissando) {
    this.hasGlissando = hasGlissando;
  }

  private boolean hasSlide = false;

  public boolean getSlide() {
    return this.hasSlide;
  }

  public void setSlide(boolean hasSlide) {
    this.hasSlide = hasSlide;
  }

  private ArrayList<Ornament> ornaments = new ArrayList<Ornament>();

  public ArrayList<Ornament> getOrnaments() {
    return this.ornaments;
  }

  public void addOrnament(Ornament ornament) {
    ornaments.add(ornament);
  }

  private ArrayList<Articulation> articulations = new ArrayList<Articulation>();

  public ArrayList<Articulation> getArticulations() {
    return this.articulations;
  }

  public void addArticulation(Articulation articulation) {
    articulations.add(articulation);
  }

  private ArrayList<Technical> technicals = new ArrayList<Technical>();

  public ArrayList<Technical> getTechnical() {
    return this.technicals;
  }

  public void addTechnical(Technical technical) {
    technicals.add(technical);
  }

  private Harmonic harmonic = null;

  public Harmonic getHarmonic() {
    return this.harmonic;
  }

  public void setHarmonic(Harmonic harmonic) {
    this.harmonic = harmonic;
  }

  private Hole hole = null;

  public Hole getHole() {
    return this.hole;
  }

  public void setHole(Hole hole) {
    this.hole = hole;
  }

  private Fingering fingering = null;

  public Fingering getFingering() {
    return this.fingering;
  }

  public void setFingering(Fingering fingering) {
    this.fingering = fingering;
  }

  private PluckFingering pluckFingering = null;

  public PluckFingering getPluckFingering() {
    return this.pluckFingering;
  }

  public void setPluckFingering(PluckFingering pluckFingering) {
    this.pluckFingering = pluckFingering;
  }

  private Fret fret = null;

  public Fret getFret() {
    return this.fret;
  }

  public void setFret(Fret fret) {
    this.fret = fret;
  }

  private MusicString musicString = null;

  public MusicString getMusicString() {
    return this.musicString;
  }

  public void setMusicString(MusicString musicString) {
    this.musicString = musicString;
  }

  boolean hasFermata = false;

  public boolean getFermata() {
    return this.hasFermata;
  }

  public void setFermata(boolean fermata) {
    this.hasFermata = fermata;
  }

  private Dynamic dynamic = null;

  public Dynamic getDynamic() {
    return this.dynamic;
  }

  public void setDynamic(Dynamic dynamic) {
    this.dynamic = dynamic;
  }

  private Arpeggiate arpeggiate = null;

  public Arpeggiate getArpeggiate() {
    return this.arpeggiate;
  }

  public void setArpeggiate(Arpeggiate arpeggiate) {
    this.arpeggiate = arpeggiate;
  }

  Lyric lyric = null;

  public Lyric getLyric() {
    return this.lyric;
  }

  public void setLyric(Lyric lyric) {
    this.lyric = lyric;
  }

  public boolean isFirstNoteOfMeasure() {
    return (this.moment.equals(Fraction.ZERO));
  }

  public boolean isFirstNoteOfPart() {
    if (!this.isFirstNoteOfMeasure()) {
      return false;
    }
    int measureNumber = this.measure.getNumber();
    if (measureNumber > 1) {
      return false;
    }
    Part part = this.measure.getPart();
    Measure measure = part.getMeasure(measureNumber);
    if (part.getMeasures().indexOf(measure) > 0) {
      return false;
    }
    return true;
  }

  public Measure getPreviousMeasure() {
    Part part = this.measure.getPart();
    int measureNumber = this.measure.getNumber();
    if ((measureNumber < 2) && (part.getMeasures().indexOf(measure) == 0)) {
      return null;
    }
    return part.getMeasure(measureNumber - 1);
  }

  public Note getPreviousNote() {
    if (this.isFirstNoteOfPart()) {
      return null;
    }
    Measure measure;
    if (this.isFirstNoteOfMeasure()) {
      measure = getPreviousMeasure();
    } else {
      measure = this.measure;
    }
    Staff staff = measure.getStaff(this.getStaffNumber());
    Voice voice = staff.getVoice(this.getVoiceNumber());
    int index = 0;
    ArrayList<MeasureElement> elements = voice.getElements();
    if (measure == this.measure) {
      for (int i = 0; i < elements.size(); i++) {
        MeasureElement element = elements.get(i);
        if (
          (element instanceof Note) &&
          (element.getMoment().equals(this.getMoment())) &&
          (element.getDuration().equals(this.getDuration()))
        ) {
          index = i - 1;
          break;
        }
      }
    } else {
      index = voice.getElements().size() - 1;
    }
    for (int i = index; i >= 0; i--) {
      MeasureElement element = elements.get(i);
      if (
        element instanceof Note &&
        element.getStaffNumber() == this.getStaffNumber() &&
        element.getVoiceNumber() == this.getVoiceNumber()
      ) {
        return (Note) element;
      }
    }
    return null;
  }
}
