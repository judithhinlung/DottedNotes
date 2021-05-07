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

public class Harmony extends MeasureElement {

  Measure measure;
  Root root;
  Bass bass;
  String kind;

  public Harmony(Measure measure, Root root, String kind)
    throws IllegalArgumentException {
    super(measure);
    if (!Utils.contains(kind, validKinds)) {
      throw new IllegalArgumentException("Invalid harmony type: " + kind);
    }
    this.root = root;
    this.kind = kind;
  }

  public Harmony(Measure measure, Bass bass, String kind)
    throws IllegalArgumentException {
    super(measure);
    if (!Utils.contains(kind, validKinds)) {
      throw new IllegalArgumentException("Invalid harmony type: " + kind);
    }
    this.bass = bass;
    this.kind = kind;
  }

  public Root getRoot() {
    return this.root;
  }

  public String getKind() {
    return this.kind;
  }

  private String[] validKinds = new String[] {
    "major",
    "minor",
    "augmented",
    "diminished",
    "dominant",
    "majorSeventh",
    "minorSeventh",
    "diminishedSeventh",
    "augmentedSeventh",
    "half-diminished",
    "majorSixth",
    "minorSixth",
    "dominantNinth",
    "majorNinth",
    "minorNinth",
    "dominant11th",
    "major11th",
    "minor11th",
    "dominant13th",
    "major13th",
    "minor13th",
    "suspendedSecond",
    "suspendedFourth",
  };
  int inversion = 0;

  public int getInversion() {
    return this.inversion;
  }

  public void setInversion(int inversion) {
    this.inversion = inversion;
  }

  Degree degree = null;

  public Degree getDegree() {
    return this.degree;
  }

  public void setDegree(Degree degree) {
    this.degree = degree;
  }

  public static class Root {

    int step;
    int alter;

    public Root(int step) {
      this.step = step;
      this.alter = 0;
    }

    public Root(int step, int alter) {
      this.step = step;
      this.alter = alter;
    }

    public int getStep() {
      return this.step;
    }

    public int getAlter() {
      return this.alter;
    }
  }

  public static class Bass extends Root {

    public Bass(int step, int alter) {
      super(step, alter);
    }
  }

  public static class Degree {

    int value;
    int alter;
    String type;

    public Degree(int value) {
      this.value = value;
    }

    public void setAlter(int alter) {
      this.alter = alter;
    }

    public void setType(String type) throws IllegalArgumentException {
      if (!Utils.contains(type, validTypes)) {
        throw new IllegalArgumentException("Invalid degree type: " + type);
      }
      this.type = type;
    }

    public int getValue() {
      return this.value;
    }

    public int getAlter() {
      return this.alter;
    }

    public String getType() {
      return this.type;
    }

    private String[] validTypes = new String[] { "add", "alter", "subtract" };
  }
}
