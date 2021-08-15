import * as React from 'react'
import Timeseries from './Timeseries'
import {useMediaQuery} from '@material-ui/core'

function App() {
  const isMobile = !useMediaQuery('(min-width:1280px)')
  const smallScreen = !useMediaQuery('(min-width:650px)')

  return (
    <>
      {
        smallScreen ?
          <img style={{maxWidth: '95%'}} src={'/images/static.png'}/>
          :
          <div style={{height: isMobile ? 1000 : 500, width: isMobile ? 600 : 1250, padding: '10px'}}>
            <Timeseries width={1200} height={400}/>
          </div>
      }
    </>
  )
}

export default App
