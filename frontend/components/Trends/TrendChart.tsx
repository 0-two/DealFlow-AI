'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendData } from '@/lib/types';

interface Props {
  data: TrendData[];
}

export default function TrendChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="month" 
          tick={{ fontSize: 12 }}
        />
        <YAxis 
          tick={{ fontSize: 12 }}
          label={{ value: 'Funding (₹ Cr)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip 
          formatter={(value: any) => `₹${value.toFixed(2)} Cr`}
          contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="total_funding" 
          stroke="#6366f1" 
          strokeWidth={2}
          name="Total Funding"
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line 
          type="monotone" 
          dataKey="deal_count" 
          stroke="#10b981" 
          strokeWidth={2}
          name="Deal Count"
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
