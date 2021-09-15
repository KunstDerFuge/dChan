import * as React from 'react'
import Timeseries from './Timeseries'
import {useMediaQuery} from '@material-ui/core'

function App() {
  const isMobile = !useMediaQuery('(min-width:1280px)')

  return (
    <>
      {
        <div style={{height: isMobile ? 1000 : 500, width: '100%', padding: '10px'}}>
          <Timeseries width={1000} height={400}/>
        </div>
      }
    </>
  )
}

export default App
