import * as React from 'react'
import Timeseries from './Timeseries'

function App() {
  const parentRef = React.useRef(null)

  return (
    <>
      {
        <div style={{minHeight: 500, width: '100%'}} ref={parentRef}>
          <Timeseries parent={parentRef}/>
        </div>
      }
    </>
  )
}

export default App
