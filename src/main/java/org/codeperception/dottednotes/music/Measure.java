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
import java.util.Map;
import java.util.Random;
import org.codeperception.dottednotes.math.Fraction;

public class Measure {

  Part part;
  private int number;

  public Measure(Part part, int number) {
    this.part = part;
    this.number = number;
    createStaves();
  }

  public Part getPart() {
    return this.part;
  }

  public int getNumber() {
    return this.number;
  }

  KeySignature keySignature = null;

  public KeySignature getKey() {
    if (this.keySignature == null) {
      return this.part.getCurrentKey(this.number);
    }
    return this.keySignature;
  }

  public void setKey(KeySignature key) {
    this.keySignature = key;
    this.part.addKeySignature(this.number, key);
  }

  TimeSignature timeSignature = null;

  public TimeSignature getTime() {
    if (this.timeSignature == null) {
      return this.part.getCurrentTime(this.number);
    }
    return this.timeSignature;
  }

  public void setTime(TimeSignature time) {
    this.timeSignature = time;
    this.part.addTimeSignature(this.number, time);
  }

  int divisions;

  public int getDivisions() {
    return part.getCurrentDivisions(this.number);
  }

  public void setDivisions(int divisions) {
    this.divisions = divisions;
    part.addDivisions(number, divisions);
  }

  /**
   * Obtains a list of the note durations found in this measure.
   */
  ArrayList<Fraction> getDurationsList() {
    ArrayList<Fraction> durations = new ArrayList<Fraction>();
    for (int i = 0; i < staves.size(); i++) {
      Staff staff = staves.get(i);
      HashMap<Integer, Voice> voices = staff.getVoices();
      for (Map.Entry<Integer, Voice> entry : voices.entrySet()) {
        Voice voice = entry.getValue();
        for (int j = 0; j < voice.getElements().size(); j++) {
          MeasureElement element = voice.getElements().get(j);
          Fraction duration = element.getDuration();
          if (element instanceof Note) {
            Note note = (Note) element;
            if (note.getTimeModification() != null) {
              TimeModification tm = note.getTimeModification();
              int normal = tm.getNormalNotes();
              int actual = tm.getActualNotes();
              duration = duration.multiply(new Fraction(normal, actual));
            }
          }
          durations.add(duration);
        }
      }
    }
    return durations;
  }

  /** Calculate the number of divisions per quarter note based on
   * a list of note durations in a measure.
   * Used to export from Score to MusicXML.
   *
   * @return  An integer representing divisions per quarter note.
   */
  public int calculateDivisions() {
    ArrayList<Fraction> durations = getDurationsList();
    int divisions = 1;
    for (int i = 0; i < durations.size(); i++) {
      Fraction current = new Fraction(1, divisions);
      Fraction next = durations.get(i).multiply(new Fraction(4, 1));
      divisions = current.getLeastCommonMultiple(next);
    }
    return divisions;
  }

  private boolean printMeasureNumber = true;

  public void setPrintMeasureNumber(boolean printMeasureNumber) {
    this.printMeasureNumber = printMeasureNumber;
  }

  private boolean isWholeMeasureRest = false;

  public void setWholeMeasureRest(boolean wholeMeasureRest) {
    this.isWholeMeasureRest = wholeMeasureRest;
  }

  boolean isCompleteMeasure() {
    Fraction measureDuration = this.getTime();
    for (int i = 0; i < staves.size(); i++) {
      Staff staff = staves.get(i);
      HashMap<Integer, Voice> voices = staff.getVoices();
      for (Map.Entry<Integer, Voice> entry : voices.entrySet()) {
        Voice voice = entry.getValue();
        Fraction currentDuration = Fraction.ZERO;
        for (int j = 0; j < voice.getElements().size(); j++) {
          MeasureElement element = voice.getElements().get(j);
          Fraction elementDuration = element.getDuration();
          if (element instanceof Note) {
            Note note = (Note) element;
            if (note.getTimeModification() != null) {
              TimeModification tm = note.getTimeModification();
              int normal = tm.getNormalNotes();
              int actual = tm.getActualNotes();
              elementDuration = elementDuration.multiply(new Fraction(normal, actual));
            }
          }
          currentDuration.add(elementDuration);
        }
        if (!measureDuration.equals(currentDuration)) {
          return false;
        }
      }
    }
    return true;
  }

  Fraction offset = Fraction.ZERO;

  public Fraction getOffset() {
    return this.offset;
  }

  ArrayList<Staff> staves = new ArrayList<Staff>();

  public void createStaves() {
    int numStaves = part.getStaves();
    for (int i = 0; i < numStaves; i++) {
      staves.add(new Staff(i + 1));
    }
  }

  public ArrayList<Staff> getStaves() {
    return this.staves;
  }

  public Staff getStaff(int staffNumber) {
    for (int i = 0; i < staves.size(); i++) {
      Staff staff = staves.get(i);
      if (staves.get(i).getNumber() == staffNumber) {
        return staff;
      }
    }
    return null;
  }

  /**
   * @param MeasureElements  ArrayList that stores any non-note and non-chord
   * object that belongs to a measure,
   * such as key and time signatures and repeat and pedal directions
   */
  ArrayList<MeasureElement> elements = new ArrayList<MeasureElement>();

  /**
   * Adds an element to a measure.
   * If element is a note or chord,
   * it is added to the corresponding Staff and Voice objects.
   *
   * @param measureElement  the measureElement to add
   */
  public void addElement(MeasureElement element) {
    element.setMoment(offset);
    if (element instanceof Backup) {
      offset = offset.subtract(element.getDuration());
    } else if (element instanceof Forward) {
      offset = offset.add(element.getDuration());
    } else {
      if ((element instanceof Note) || (element instanceof Chord)) {
        int staffNumber = element.getStaffNumber();
        int voiceNumber = element.getVoiceNumber();
        Staff staff = getStaff(staffNumber);
        if (!staff.hasVoice(voiceNumber)) {
          staff.addVoice(new Voice(voiceNumber));
        }
        Voice voice = staff.getVoice(voiceNumber);
        voice.addElement(element);
      } else {
        this.elements.add(element);
      }
      offset = offset.add(element.getDuration());
    }
  }

  /**
   * Removes an element from a measure.
   * If element is a note or chord,
   * it is removed fromthe corresponding Staff and Voice objects.
   *
   * @param measureElement  the measureElement to remove
   */
  public void removeElement(MeasureElement element) {
    if ((element instanceof Note) || (element instanceof Chord)) {
      int staffNumber = element.getStaffNumber();
      int voiceNumber = element.getVoiceNumber();
      Staff staff = getStaff(staffNumber);
      Voice voice = staff.getVoice(voiceNumber);
      voice.removeElement(element);
      offset = offset.subtract(element.getDuration());
    } else if (element instanceof Backup) {
      offset = offset.add(element.getDuration());
    } else if (element instanceof Forward) {
      offset = offset.subtract(element.getDuration());
    } else {
      for (int i = 0; i < elements.size(); i++) {
        MeasureElement current = elements.get(i);
        if (
          (current.getClass() == element.getClass()) &&
          (current.getMoment().equals(element.getMoment()))
        ) {
          elements.remove(i);
        }
        break;
      }
    }
  }

  /**
   * Returns all elements found in this measure,
   * sorted by duration from earliest to latest in time.
   */
  public ArrayList<MeasureElement> getMeasureElements() {
    ArrayList<MeasureElement> elementsList = new ArrayList<MeasureElement>();
    for (int i = 0; i < this.elements.size(); i++) {
      elementsList.add(this.elements.get(i));
    }
    for (int i = 0; i < staves.size(); i++) {
      Staff staff = staves.get(i);
      HashMap<Integer, Voice> voices = staff.getVoices();
      for (Map.Entry<Integer, Voice> entry : voices.entrySet()) {
        Voice voice = entry.getValue();
        ArrayList<MeasureElement> voiceElements = voice.getElements();
        adjustDurationsForGraceNotes(voiceElements);
        for (int j = 0; j < voiceElements.size(); j++) {
          MeasureElement element = voice.getElements().get(j);
          elementsList.add(element);
        }
      }
    }
    randomizedQuickSort(elementsList, 0, elementsList.size() - 1);
    return elementsList;
  }

  void adjustDurationsForGraceNotes(ArrayList<MeasureElement> elements) {
    Fraction totalGraceDuration = Fraction.ZERO;
    boolean isInGrace = false;
    for (int i = 0; i < elements.size(); i++) {
      MeasureElement element = elements.get(i);
      if (element instanceof Note) {
        Note note = (Note) element;
        if (note.getGrace() != null) {
          Fraction graceDuration = note.getDurationFromType(note.getType()).divide(2);
          if (isInGrace) {
            note.setMoment(note.getMoment().add(totalGraceDuration));
          } else {
            isInGrace = true;
          }
          note.setDuration(graceDuration);
          totalGraceDuration = totalGraceDuration.add(graceDuration);
        } else if (isInGrace) {
          Fraction startMoment = note.getMoment().add(totalGraceDuration);
          note.setMoment(startMoment);
          note.setDuration(note.getDuration().subtract(totalGraceDuration));
          isInGrace = false;
          totalGraceDuration = Fraction.ZERO;
        }
      }
    }
  }

  /**
   * Obtains a partition of measure elements that start at the same moment in time
   * based on the given range l,r
   */
  private static int[] partition3(ArrayList<MeasureElement> a, int l, int r) {
    int m1 = l;
    int m2 = m1;
    int j = m2;
    MeasureElement x = a.get(l);
    for (int i = l + 1; i <= r; i++) {
      if (a.get(i).getMoment().compareTo(x.getMoment()) == 0) {
        m2++;
        j++;
        MeasureElement t = a.get(i);
        a.set(i, a.get(m2));
        a.set(m2, t);
        if (a.get(i).getMoment().compareTo(a.get(m2).getMoment()) < 0) {
          t = a.get(j);
          a.set(j, a.get(i));
          a.set(i, t);
        }
      } else if (a.get(i).getMoment().compareTo(x.getMoment()) < 0) {
        j++;
        MeasureElement t = a.get(i);
        a.set(i, a.get(j));
        a.set(j, t);
      }
    }
    int index2 = j;
    for (int i = m1; i <= m2; i++) {
      MeasureElement t = a.get(index2);
      a.set(index2, a.get(i));
      a.set(i, t);
      index2 -= 1;
    }
    if (m1 == m2) {
      m1 = j;
      m2 = j;
    } else {
      m1 = j - (m2 - m1);
      m2 = j;
    }
    int[] m = { m1, m2 };
    return m;
  }

  // Variable to generate a random value
  private static Random random = new Random();

  /**
   * Sorts measure elements by moment in time
   */

  private static void randomizedQuickSort(ArrayList<MeasureElement> a, int l, int r) {
    if (l >= r) {
      return;
    }
    int k = random.nextInt(r - l + 1) + l;
    MeasureElement t = a.get(l);
    a.set(l, a.get(k));
    a.set(k, t);
    int[] m = partition3(a, l, r);
    randomizedQuickSort(a, l, m[0] - 1);
    randomizedQuickSort(a, m[1] + 1, r);
  }
}
