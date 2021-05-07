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

public class Score {

  ArrayList<Part> parts;

  public Score() {
    this.parts = new ArrayList<Part>();
  }

  public ArrayList<Part> getParts() {
    return this.parts;
  }

  public Part getPart(String id) {
    ArrayList<Part> parts = this.parts;
    for (int i = 0; i < parts.size(); i++) {
      Part part = parts.get(i);
      if (part.getId().equals(id)) {
        return part;
      }
    }
    return null;
  }

  public void addPart(Part part) {
    this.parts.add(part);
  }

  public int getDivisions() {
    if (this.getParts().size() < 1) {
      return 0;
    }
    Part firstPart = this.parts.get(0);
    return firstPart.getCurrentDivisions(1);
  }

  String workNumber;

  public String getWorkNumber() {
    return this.workNumber;
  }

  public void setWorkNumber(String workNumber) {
    this.workNumber = workNumber;
  }

  String workTitle;

  public String getWorkTitle() {
    return this.workTitle;
  }

  public void setWorkTitle(String workTitle) {
    this.workTitle = workTitle;
  }

  String opus;

  public String getOpus() {
    return this.opus;
  }

  public void setOpus(String opus) {
    this.opus = opus;
  }

  String movementNumber;

  public String getMovementNumber() {
    return this.movementNumber;
  }

  public void setMovementNumber(String movementNumber) {
    this.movementNumber = movementNumber;
  }

  String movementTitle;

  public String getMovementTitle() {
    return this.movementTitle;
  }

  public void setMovementTitle(String movementTitle) {
    this.movementTitle = movementTitle;
  }

  String composer;

  public String getComposer() {
    return this.composer;
  }

  public void setComposer(String composer) {
    this.composer = composer;
  }

  String lyricist;

  public String getLyricist() {
    return this.lyricist;
  }

  public void setLyricist(String lyricist) {
    this.lyricist = lyricist;
  }

  String rights;

  public String getRights() {
    return this.rights;
  }

  public void addRights(String rights) {
    StringBuilder s = new StringBuilder();
    String originalRights = this.rights;
    s.append(originalRights);
    s.append(rights);
    this.rights = s.toString();
  }

  String encodingDate;

  public String getEncodingDate() {
    return this.encodingDate;
  }

  public void setEncodingDate(String date) {
    this.encodingDate = date;
  }

  String encoder;

  public String getEncoder() {
    return this.encoder;
  }

  public void setEncoder(String encoder) {
    this.encoder = encoder;
  }

  String encodingSoftware;

  public String getEncodingSoftware() {
    return this.encodingSoftware;
  }

  public void setEncodingSoftware(String software) {
    this.encodingSoftware = software;
  }
}
