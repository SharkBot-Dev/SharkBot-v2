import { connectDB } from '@/lib/mongodb';
import { Long } from 'mongodb';
import { NextResponse } from 'next/server';
import crypto from 'crypto';
import { getChannels, sendMessage } from '@/lib/discord/fetch';

export async function POST(request: Request, { params }: { params: Promise<{ guildid: string }> }) {
    const signature = request.headers.get('x-topgg-signature');
    if (!signature) {
        return NextResponse.json({ status: 'Unauthorized' }, { status: 401 });
    }

    const { guildid } = await params;

    try {
        const db = await connectDB();
        const setting = await db.db("MainTwo").collection("TopggVoteAlert").findOne({
            guild_id: Long.fromString(guildid)
        });

        if (!setting || !setting.apikey) {
            return NextResponse.json({ status: 'received' }, { status: 200 });
        }

        const rawBody = await request.text();

        const sigParams = new URLSearchParams(signature.replace(/,/g, '&'));
        const t = sigParams.get('t');
        const v1 = sigParams.get('v1');

        if (!t || !v1) {
            return new NextResponse('Invalid signature format', { status: 400 });
        }

        const expectedSignature = crypto
            .createHmac('sha256', setting.apikey)
            .update(`${t}.${rawBody}`)
            .digest('hex');

        if (v1 !== expectedSignature) {
            return new NextResponse('Unauthorized', { status: 401 });
        }

        const data = JSON.parse(rawBody);
        
        const guild_channels = await getChannels(guildid);
        const channelsData = Array.isArray((guild_channels as any).data)
            ? (guild_channels as any).data
            : guild_channels;

        if (!channelsData.some((c: any) => c.id === (setting.channel_id as Long).toString())) return NextResponse.json({ status: 'received' }, { status: 200 });

        await sendMessage(setting.channel_id, {
            embeds: [
                {
                    description: (setting.text as string).replaceAll("{user}", `<@${data.data.user.platform_id}>`),
                    color: 0x57f287
                }
            ]
        })

        return NextResponse.json({ status: 'received' }, { status: 200 });

    } catch (error) {
        console.error('Webhook Error:', error);
        return new NextResponse('VoteError', { status: 500 });
    }
}

export async function GET() {
    return new NextResponse('Method Not Allowed', { status: 405 });
}