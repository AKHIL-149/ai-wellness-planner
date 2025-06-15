// frontend/src/pages/Login.jsx

import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from '../hooks/useForm';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Card from '../components/common/Card';
import { validators } from '../utils';
import { EyeIcon, EyeSlashIcon, UserIcon, LockClosedIcon } from '@heroicons/react/24/outline';

const Login = () => {
  const [showPassword, setShowPassword] = useState(false);
  const { login, loading, error, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const validationRules = {
    email: [validators.required, validators.email],
    password: [validators.required],
  };

  const {
    values,
    errors,
    handleChange,
    handleSubmit,
    getFieldProps,
    getFieldState,
  } = useForm({
    email: '',
    password: '',
    remember_me: false,
  }, validationRules);

  const handleLogin = handleSubmit(async (formData) => {
    const result = await login(formData);
    if (result.success) {
      navigate(from, { replace: true });
    }
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo and Header */}
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl mx-auto mb-4 flex items-center justify-center">
            <span className="text-white font-bold text-2xl">AW</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Welcome back</h2>
          <p className="mt-2 text-gray-600">
            Sign in to your AI Wellness account
          </p>
        </div>

        {/* Login Form */}
        <Card className="mt-8">
          <form className="space-y-6" onSubmit={handleLogin}>
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <Input
              label="Email address"
              type="email"
              autoComplete="email"
              leftIcon={UserIcon}
              {...getFieldProps('email')}
              {...getFieldState('email')}
            />

            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                leftIcon={LockClosedIcon}
                {...getFieldProps('password')}
                {...getFieldState('password')}
                rightIcon={showPassword ? EyeSlashIcon : EyeIcon}
              />
              <button
                type="button"
                className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="w-5 h-5" />
                ) : (
                  <EyeIcon className="w-5 h-5" />
                )}
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember_me"
                  type="checkbox"
                  checked={values.remember_me}
                  onChange={handleChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                  Remember me
                </label>
              </div>

              <div className="text-sm">
                <Link
                  to="/forgot-password"
                  className="font-medium text-blue-600 hover:text-blue-500"
                >
                  Forgot your password?
                </Link>
              </div>
            </div>

            <Button
              type="submit"
              fullWidth
              loading={loading}
              size="lg"
            >
              Sign in
            </Button>

            <div className="text-center">
              <span className="text-sm text-gray-600">
                Don't have an account?{' '}
                <Link
                  to="/register"
                  className="font-medium text-blue-600 hover:text-blue-500"
                >
                  Sign up now
                </Link>
              </span>
            </div>
          </form>
        </Card>

        {/* Demo Account */}
        <div className="text-center">
          <p className="text-sm text-gray-500 mb-2">Try the demo account:</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setValue('email', 'demo@aiw ellness.com');
              setValue('password', 'demo123');
            }}
          >
            Use Demo Account
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Login;