/**
 * ui-shared — shared component and type exports.
 *
 * Import components directly:
 *   import FindingCard from "ui-shared/components/FindingCard"
 *   import ReportView  from "ui-shared/components/ReportView"
 *   import NavBar      from "ui-shared/components/NavBar"
 *   import ScanSpinner from "ui-shared/components/ScanSpinner"
 *
 * Import types:
 *   import type { Finding, Report, Severity } from "ui-shared/components/FindingCard/types"
 *
 * Import styles:
 *   import "ui-shared/styles/variables.css"
 *   import "ui-shared/styles/base.css"
 */

export { FindingCard } from "./components/FindingCard";
export type { FindingCardProps } from "./components/FindingCard";

export { ReportView } from "./components/ReportView";
export type { ReportViewProps } from "./components/ReportView";

export { NavBar } from "./components/NavBar";
export type { NavBarProps } from "./components/NavBar";

export { ScanSpinner } from "./components/ScanSpinner";
export type { ScanSpinnerProps, ScanStatus } from "./components/ScanSpinner";

export type { Finding, Report, Severity } from "./components/FindingCard/types";
