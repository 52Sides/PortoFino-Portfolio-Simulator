declare module 'react-plotly.js' {
  import { Component } from 'react'
  import type { Data, Layout, Config } from 'plotly.js'

  interface PlotProps {
    data: Data[]
    layout?: Partial<Layout>
    config?: Partial<Config>
    style?: React.CSSProperties
    onClick?: (event: any) => void
    onHover?: (event: any) => void
    onUnhover?: (event: any) => void
    [key: string]: unknown
  }

  export default class Plot extends Component<PlotProps> {}
}
