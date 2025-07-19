import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import Gallery from './components/Gallery';
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Router>
      <Switch>
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        <PrivateRoute path="/dashboard" component={Dashboard} />
        <PrivateRoute path="/galleries/:id" component={Gallery} />
      </Switch>
    </Router>
  );
}

export default App;
