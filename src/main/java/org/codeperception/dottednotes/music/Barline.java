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

public class Barline extends MeasureElement {

  Measure measure;
  String type;
  String location;

  public Barline(Measure measure) {
    super(measure);
    this.location = "left";
  }

  public Barline(Measure measure, String location) throws IllegalArgumentException {
    super(measure);
    if (!Utils.contains(location, validLocations)) {
      throw new IllegalArgumentException("Invalid barline location: " + location);
    }
    this.location = location;
  }

  public String getLocation() {
    return this.location;
  }

  public void setLocation(String location) throws IllegalArgumentException {
    if (!Utils.contains(location, validLocations)) {
      throw new IllegalArgumentException("Invalid barline location: " + location);
    }
    this.location = location;
  }

  private String[] validLocations = new String[] { "left", "middle", "right" };
  private Ending ending;

  public Ending getEnding() {
    return this.ending;
  }

  public void setEnding(Ending ending) {
    this.ending = ending;
  }

  private boolean segno = false;

  public boolean getSegno() {
    return this.segno;
  }

  public void setSegno(boolean segno) {
    this.segno = segno;
  }

  private boolean coda = false;

  public boolean getCoda() {
    return this.coda;
  }

  public void setCoda(boolean coda) {
    this.coda = coda;
  }

  private boolean fermata = false;

  public boolean getFermata() {
    return this.fermata;
  }

  public void setFermata(boolean fermata) {
    this.fermata = fermata;
  }

  private Repeat repeat = null;

  public Repeat getRepeat() {
    return this.repeat;
  }

  public void setRepeat(Repeat repeat) {
    this.repeat = repeat;
  }

  public boolean isEndingStart() {
    return (
      (this.getLocation().equals("left")) && (this.getEnding().getType().equals("start"))
    );
  }

  public boolean isEndingStop() {
    return (
      this.getLocation().equals("right") && this.getEnding().getType().equals("stop")
    );
  }
}
