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

import org.codeperception.dottednotes.math.Fraction;

public class Sound extends MeasureElement {

  Measure measure = null;

  public Sound(Measure measure) {
    super(measure);
  }

  Instrument instrument = null;

  public Instrument getInstrument() {
    return this.instrument;
  }

  public void setInstrument(Instrument instrument) {
    this.instrument = instrument;
  }

  int velocity = 64;

  public int getVelocity() {
    return this.velocity;
  }

  public void setVelocity(int velocity) {
    this.velocity = velocity;
  }

  int tempo = 100;

  public int getTempo() {
    return this.tempo;
  }

  public void setTempo(int tempo) {
    this.tempo = tempo;
  }

  boolean dacapo = false;

  public boolean getDacapo() {
    return this.dacapo;
  }

  public void setDacapo(boolean dacapo) {
    this.dacapo = dacapo;
  }

  boolean segno = false;

  public boolean getSegno() {
    return this.segno;
  }

  public void setSegno(boolean segno) {
    this.segno = segno;
  }

  boolean dalsegno = false;

  public boolean getDalsegno() {
    return this.dalsegno;
  }

  public void setDalsegno(boolean dalsegno) {
    this.dalsegno = dalsegno;
  }

  boolean coda = false;

  public boolean getCoda() {
    return this.coda;
  }

  public void setCoda(boolean coda) {
    this.coda = coda;
  }

  boolean tocoda = false;

  public boolean getTocoda() {
    return this.tocoda;
  }

  public void setTocoda(boolean tocoda) {
    this.tocoda = tocoda;
  }

  boolean fine = false;

  public boolean getFine() {
    return this.fine;
  }

  public void setFine(boolean fine) {
    this.fine = fine;
  }

  boolean isPizzicato = false;

  public boolean getPizzicato() {
    return this.isPizzicato;
  }

  public void setPizzicato(boolean pizz) {
    this.isPizzicato = pizz;
  }

  boolean forwardRepeat = false;

  public boolean getForwardRepeat() {
    return this.forwardRepeat;
  }

  public void setForwardRepeat(boolean repeat) {
    this.forwardRepeat = repeat;
  }

  Fraction offset = Fraction.ZERO;

  public Fraction getOffset() {
    return this.offset;
  }

  public void setOffset(Fraction offset) {
    this.offset = offset;
  }
}
