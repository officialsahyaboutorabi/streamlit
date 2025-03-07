/**
 * Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React from "react"

import "@testing-library/jest-dom"
import { screen } from "@testing-library/react"

import { render } from "@streamlit/lib/src/test_util"
import { Progress as ProgressProto } from "@streamlit/lib/src/proto"

import Progress, { ProgressProps } from "./Progress"

const getProps = (
  propOverrides: Partial<ProgressProps> = {}
): ProgressProps => ({
  element: ProgressProto.create({
    value: 50,
  }),
  width: 0,
  ...propOverrides,
})

describe("Progress component", () => {
  it("renders without crashing", () => {
    render(<Progress {...getProps()} />)

    const progressElement = screen.getByTestId("stProgress")
    expect(progressElement).toBeInTheDocument()
    expect(progressElement).toHaveClass("stProgress")
  })

  it("sets the value correctly", () => {
    render(<Progress {...getProps({ width: 100 })} />)

    expect(screen.getByTestId("stProgress")).toBeInTheDocument()
    expect(screen.getByRole("progressbar")).toHaveAttribute(
      "aria-valuenow",
      "50"
    )
  })
})
