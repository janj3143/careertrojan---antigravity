import React, { useMemo } from "react";
import Plot from "react-plotly.js";
import type { CoveyActionLens } from "../../lib/chartLensTypes";

type CoveyPlanePlotlyProps = {
  covey: CoveyActionLens;
  filterAxisKey?: string;
  selectedActionId?: string;
  onSelectAction?: (actionId: string | null) => void;
  height?: number;
};

export function CoveyPlanePlotly({
  covey,
  filterAxisKey,
  selectedActionId,
  onSelectAction,
  height = 520,
}: CoveyPlanePlotlyProps) {
  const actions = useMemo(() => {
    if (!filterAxisKey) {
      return covey.actions;
    }
    return covey.actions.filter((action) => Object.prototype.hasOwnProperty.call(action.axis_effects, filterAxisKey));
  }, [covey.actions, filterAxisKey]);

  const points = useMemo(() => {
    return {
      x: actions.map((action) => action.effort_friction),
      y: actions.map((action) => action.impact_potential),
      text: actions.map((action) => action.title),
      custom: actions.map((action) => ({
        action_id: action.action_id,
        axis_effects: action.axis_effects,
        confidence: action.confidence,
        quadrant: action.quadrant,
      })),
    };
  }, [actions]);

  return (
    <Plot
      data={[
        {
          type: "scatter",
          mode: "markers",
          x: points.x,
          y: points.y,
          text: points.text,
          customdata: points.custom,
          hovertemplate:
            "Action: %{text}<br>" +
            `${covey.axis_spec.x_label}: %{x}<br>` +
            `${covey.axis_spec.y_label}: %{y}<extra></extra>`,
          marker: { size: 10, opacity: 0.85 },
          name: "Actions",
        },
      ]}
      layout={{
        title: covey.title,
        height,
        xaxis: { title: covey.axis_spec.x_label, range: [0, 100] },
        yaxis: { title: covey.axis_spec.y_label, range: [0, 100] },
        shapes: [
          { type: "line", x0: 50, x1: 50, y0: 0, y1: 100, xref: "x", yref: "y" },
          { type: "line", x0: 0, x1: 100, y0: 50, y1: 50, xref: "x", yref: "y" },
        ],
        hovermode: "closest",
        margin: { l: 60, r: 20, t: 60, b: 60 },
      }}
      config={{ displaylogo: false }}
      style={{ width: "100%" }}
      useResizeHandler
      onClick={(event: any) => {
        const clickedId = event?.points?.[0]?.customdata?.action_id ?? null;
        if (!onSelectAction) {
          return;
        }
        onSelectAction(clickedId === selectedActionId ? null : clickedId);
      }}
    />
  );
}
