declare module 'react-plotly.js' {
  import { Component } from 'react'
  import type { Data, Layout, Config } from 'plotly.js'

  interface PlotProps {
    data: Data[]
    layout?: Partial<Layout>
    config?: Partial<Config>
    style?: React.CSSProperties
    onClick?: (event: unknown) => void
    onHover?: (event: unknown) => void
    onUnhover?: (event: unknown) => void
    [key: string]: unknown
  }

  export default class Plot extends Component<PlotProps> {}
}
