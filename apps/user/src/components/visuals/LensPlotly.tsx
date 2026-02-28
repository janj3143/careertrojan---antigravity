import React, { useMemo } from "react";
import Plot from "react-plotly.js";
import type { ChartLens } from "../../lib/chartLensTypes";

type LensPlotlyProps = {
  lens: ChartLens;
  height?: number;
};

export function LensPlotly({ lens, height = 520 }: LensPlotlyProps) {
  const data = useMemo(() => {
    const traces: any[] = [];

    if (lens.density) {
      traces.push({
        type: "heatmap",
        x: lens.density.x_edges,
        y: lens.density.y_edges,
        z: lens.density.z,
        hovertemplate: "Count: %{z}<extra></extra>",
        name: "Density",
        showscale: true,
      });
    }

    if (lens.sample_points?.length) {
      traces.push({
        type: "scattergl",
        mode: "markers",
        x: lens.sample_points.map((p) => p.x),
        y: lens.sample_points.map((p) => p.y),
        text: lens.sample_points.map((p) => p.label ?? p.id ?? ""),
        customdata: lens.sample_points.map((p) => p.meta ?? {}),
        hovertemplate: `${lens.x.label}: %{x}<br>${lens.y.label}: %{y}<br>%{text}<extra></extra>`,
        marker: { size: 6, opacity: 0.35 },
        name: "Sample",
      });
    }

    if (lens.trend) {
      const trend = lens.trend;
      if (trend.y_lo?.length && trend.y_hi?.length) {
        traces.push({
          type: "scatter",
          mode: "lines",
          x: [...trend.x, ...trend.x.slice().reverse()],
          y: [...trend.y_lo, ...trend.y_hi.slice().reverse()],
          fill: "toself",
          hoverinfo: "skip",
          line: { width: 0 },
          opacity: 0.2,
          name: "Band",
        });
      }

      traces.push({
        type: "scatter",
        mode: "lines",
        x: trend.x,
        y: trend.y,
        line: { width: 3 },
        hovertemplate: `${lens.x.label}: %{x}<br>${lens.y.label}: %{y}<extra></extra>`,
        name: `Trend (${trend.method})`,
      });
    }

    const addExceptions = (items: typeof lens.sample_points, name: string) => {
      if (!items?.length) {
        return;
      }
      traces.push({
        type: "scatter",
        mode: "markers",
        x: items.map((p) => p.x),
        y: items.map((p) => p.y),
        text: items.map((p) => p.label ?? p.id ?? ""),
        customdata: items.map((p) => p.meta ?? {}),
        hovertemplate: `${lens.x.label}: %{x}<br>${lens.y.label}: %{y}<br>%{text}<extra></extra>`,
        marker: { size: 9, opacity: 0.9 },
        name,
      });
    };

    addExceptions(lens.exceptions_above, "Above-trend");
    addExceptions(lens.exceptions_below, "Below-trend");

    return traces;
  }, [lens]);

  const layout = useMemo(() => {
    const shapes: any[] = [];

    if (lens.quadrants) {
      shapes.push(
        { type: "line", x0: lens.quadrants.x_split, x1: lens.quadrants.x_split, y0: 0, y1: 1, xref: "x", yref: "paper" },
        { type: "line", x0: 0, x1: 1, y0: lens.quadrants.y_split, y1: lens.quadrants.y_split, xref: "paper", yref: "y" }
      );
    }

    return {
      title: lens.title,
      height,
      xaxis: { title: lens.x.label, type: lens.x.scale === "log" ? "log" : "linear" },
      yaxis: { title: lens.y.label, type: lens.y.scale === "log" ? "log" : "linear" },
      shapes,
      hovermode: "closest",
      margin: { l: 60, r: 20, t: 60, b: 60 },
    };
  }, [lens, height]);

  return (
    <Plot
      data={data}
      layout={layout}
      useResizeHandler
      style={{ width: "100%" }}
      config={{ displaylogo: false }}
    />
  );
}
